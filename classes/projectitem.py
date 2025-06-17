
import os
import subprocess
import sys
import re
import json
import asyncio

from classes.lazyload import Lazyload
from classes.gitter import Gitter

class Projectitem(Lazyload):

    def __init__(self, owner=None, number=None):
        super().__init__()

    @classmethod 
    def get_project_item_history(cls, item_id:str) -> dict:
        query = '''
        query($itemId: ID!) {
          node(id: $itemId) {
            ... on ProjectV2Item {
              id
              content {
                ... on Issue { title number }
                ... on PullRequest { title number }
                ... on DraftIssue { title }
              }
              project {
                title
              }
              fieldValues(first: 50) {
                nodes {
                  ... on ProjectV2ItemFieldTextValue {
                    field { 
                      ... on ProjectV2FieldCommon { name dataType } 
                    }
                    text
                    updatedAt
                    creator { login }
                  }
                  ... on ProjectV2ItemFieldDateValue {
                    field { 
                      ... on ProjectV2FieldCommon { name dataType } 
                    }
                    date
                    updatedAt
                    creator { login }
                  }
                  ... on ProjectV2ItemFieldSingleSelectValue {
                    field { 
                      ... on ProjectV2FieldCommon { name dataType } 
                    }
                    name
                    updatedAt
                    creator { login }
                  }
                  ... on ProjectV2ItemFieldNumberValue {
                    field { 
                      ... on ProjectV2FieldCommon { name dataType } 
                    }
                    number
                    updatedAt
                    creator { login }
                  }
                  ... on ProjectV2ItemFieldIterationValue {
                    field { 
                      ... on ProjectV2FieldCommon { name dataType } 
                    }
                    title
                    startDate
                    updatedAt
                    creator { login }
                  }
                }
              }
              updatedAt
              createdAt
              creator {
                login
              }
            }
          }
        }
        '''

        # Use the correct format for GitHub CLI with GraphQL variables
        result = subprocess.run([
            'gh', 'api', 'graphql',
            '-f', 'query=' + query.strip(),
            '-f', f'itemId={item_id}'
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            sys.exit(1)

        return json.loads(result.stdout)
    
    @classmethod
    def get_status_change_history(cls, item_id:str) -> dict:
        """
        Get the history of status changes for a specific project item.
        This uses the issue/PR timeline API to get status changes.
        """
        # First, determine if this is an issue or PR and get its number
        query = '''
        query($itemId: ID!) {
          node(id: $itemId) {
            ... on ProjectV2Item {
              id
              content {
                ... on Issue { 
                  number 
                  repository { nameWithOwner }
                  url
                }
                ... on PullRequest { 
                  number 
                  repository { nameWithOwner }
                  url
                }
              }
              project {
                title
                number
              }
              fieldValues(first: 50) {
                nodes {
                  ... on ProjectV2ItemFieldSingleSelectValue {
                    field { 
                      ... on ProjectV2FieldCommon { name } 
                    }
                    name
                    updatedAt
                  }
                }
              }
            }
          }
        }
        '''

        # Get basic info about the item
        result = subprocess.run([
            'gh', 'api', 'graphql',
            '-f', f'query={query}',
            '-f', f'itemId={item_id}'
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            sys.exit(1)

        item_data = json.loads(result.stdout)
        content = item_data.get('data', {}).get('node', {}).get('content', {})

        # If content exists, we have an issue or PR
        if not content:
            return {"error": "Could not determine issue or PR number for this project item"}

        repo = content.get('repository', {}).get('nameWithOwner')
        number = content.get('number')

        if not repo or not number:
            return {"error": "Missing repository or number information"}

        # Get project field changes from the timeline
        # This uses the REST API to get detailed timeline data
        timeline_cmd = [
            'gh', 'api',
            f'repos/{repo}/issues/{number}/timeline',
            '-H', 'Accept: application/vnd.github.mockingbird-preview+json'
        ]

        timeline_result = subprocess.run(timeline_cmd, capture_output=True, text=True)

        if timeline_result.returncode != 0:
            print(f"Error fetching timeline: {timeline_result.stderr}")
            return {"error": "Failed to fetch timeline data"}

        timeline_data = json.loads(timeline_result.stdout)

        # Filter for project card events that might indicate status changes
        status_changes = []
        for event in timeline_data:
            if event.get('event') in ['converted_note_to_issue', 'moved_columns_in_project', 'added_to_project', 'converted_to_discussion']:
                status_changes.append({
                    "date": event.get('created_at'),
                    "actor": event.get('actor', {}).get('login'),
                    "event_type": event.get('event'),
                    "column_from": event.get('previous_column_name'),
                    "column_to": event.get('column_name'),
                    "project": event.get('project_card', {}).get('project_id')
                })

        # Return combined data
        return {
            "item_info": item_data,
            "status_changes": status_changes
        }
    

    def get_created_date(self) -> str:
        """
        Get the creation date of a project item.

        Args:
            project_id: The ID of the project
            item_id: The ID of the project item

        Returns:
            str: The creation date in ISO format (YYYY-MM-DD)
        """
        query = '''
        query($itemId: ID!) {
          node(id: $itemId) {
            ... on ProjectV2Item {
              createdAt
            }
          }
        }
        '''

        item_id = self.get('id')

        result = subprocess.run([
            'gh', 'api', 'graphql',
            '-f', f'query={query}',
            '-f', f'itemId={item_id}'
        ], capture_output=True, text=True)

        if result.returncode != 0:
            return ""

        response_data = json.loads(result.stdout)
        created_at = response_data.get('data', {}).get('node', {}).get('createdAt', '')

        # Return just the date portion (YYYY-MM-DD)
        if created_at:
            self.set('created_at', created_at.split('T')[0])
            return self.get('created_at')
        return ""


    def infer_start_date(cls, project_id: str, item_id: str, field_id: str, value: str) -> bool:
        """
        Set a date field value for a project item.

        Args:
            project_id: The ID of the project
            item_id: The ID of the project item
            field_id: The ID of the date field
            value: The date value in YYYY-MM-DD format

        Returns:
            bool: True if successful, False otherwise
        """
        mutation = '''
        mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $dateValue: Date!) {
          updateProjectV2ItemFieldValue(
            input: {
              projectId: $projectId
              itemId: $itemId
              fieldId: $fieldId
              value: { date: $dateValue }
            }
          ) {
            projectV2Item {
              id
            }
          }
        }
        '''

        result = subprocess.run([
            'gh', 'api', 'graphql',
            '-f', f'query={mutation}',
            '-f', f'projectId={project_id}',
            '-f', f'itemId={item_id}',
            '-f', f'fieldId={field_id}',
            '-f', f'dateValue={value}'
        ], capture_output=True, text=True)

        if result.returncode != 0:
            return False

        response_data = json.loads(result.stdout)
        return 'data' in response_data and 'updateProjectV2ItemFieldValue' in response_data['data']