from gh_tt.classes.semver import SemverVersion


def test_prerelease_version_comparison():
    # Test that alpha.10 > alpha.9
    v9 = SemverVersion(1, 3, 0, "alpha.9", None)
    v10 = SemverVersion(1, 3, 0, "alpha.10", None)
    
    assert v9 < v10
    assert not (v10 < v9)
    
    # Test various prerelease identifiers
    assert SemverVersion(1, 0, 0, "alpha", None) < SemverVersion(1, 0, 0, "beta", None)
    assert SemverVersion(1, 0, 0, "alpha.1", None) < SemverVersion(1, 0, 0, "alpha.2", None)
    assert SemverVersion(1, 0, 0, "alpha.1", None) < SemverVersion(1, 0, 0, "alpha.10", None)
    assert SemverVersion(1, 0, 0, "alpha.beta", None) < SemverVersion(1, 0, 0, "beta", None)
    
    # Test numeric vs non-numeric identifiers
    assert SemverVersion(1, 0, 0, "1.alpha", None) < SemverVersion(1, 0, 0, "alpha", None)
    
    # Test different length but same prefix
    assert SemverVersion(1, 0, 0, "alpha", None) < SemverVersion(1, 0, 0, "alpha.1", None)


def test_build_version_comparison():
    # Test that +10 > +9
    v9 = SemverVersion(1, 3, 0, None, "9")
    v10 = SemverVersion(1, 3, 0, None, "10")
    
    assert v9 < v10
    assert not (v10 < v9)
    
    # Test build identifiers with complex structures
    assert SemverVersion(1, 0, 0, None, "1.abc") < SemverVersion(1, 0, 0, None, "2.abc")
    assert SemverVersion(1, 0, 0, None, "1.2") < SemverVersion(1, 0, 0, None, "1.10")
    assert SemverVersion(1, 0, 0, None, "alpha.1") < SemverVersion(1, 0, 0, None, "alpha.2")
    assert SemverVersion(1, 0, 0, None, "alpha.1") < SemverVersion(1, 0, 0, None, "alpha.10")
    
    # Test numeric vs non-numeric identifiers
    assert SemverVersion(1, 0, 0, None, "1.alpha") < SemverVersion(1, 0, 0, None, "alpha")
    
    # Test prerelease takes precedence over build
    assert SemverVersion(1, 0, 0, "alpha", "999") < SemverVersion(1, 0, 0, None, "1")
    
    # Test complex case with prerelease and build
    assert SemverVersion(1, 0, 0, "alpha.9", "1") < SemverVersion(1, 0, 0, "alpha.10", "1")
