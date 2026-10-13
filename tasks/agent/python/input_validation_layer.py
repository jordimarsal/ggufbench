ID = "input_validation_layer"
LANG = "python"
GOAL = "Crea un mòdul input_validator.py amb una classe InputValidator que implementi validació per whitelist (només valors acceptats) i una taxonomia d'errors clara. Ha de tenir els mètodes: validate_email(email), validate_age(age), validate_status(status). Status ha de ser whitelist ['active', 'inactive', 'pending']. Els tests verifiquen el comportament correcte i les excepcions."
INITIAL_FILES = {
    "solution.py": "# Solution buida - cal implementar-ho tot",
    "test_solution.py": "from input_validator import *\n\n# Test email validation\nv = InputValidator()\nassert v.validate_email('user@example.com') == True\ntry:\n    v.validate_email('not-an-email')\n    assert False, \"Should raise ValueError\"\nexcept ValueError as e:\n    assert 'invalid' in str(e).lower() or 'email' in str(e).lower(), f\"Wrong error message: {e}\"\n\n# Test age validation\nassert v.validate_age(25) == True\ntry:\n    v.validate_age(-1)\n    assert False, \"Should raise ValueError\"\nexcept ValueError as e:\n    assert 'age' in str(e).lower(), f\"Wrong error message: {e}\"\n\n# Test status whitelist\nassert v.validate_status('active') == True\nassert v.validate_status('inactive') == True\nassert v.validate_status('pending') == True\ntry:\n    v.validate_status('deleted')\n    assert False, \"Should raise ValueError\"\nexcept ValueError as e:\n    assert 'status' in str(e).lower(), f\"Wrong error message: {e}\"\n\nprint('OK')"
}
TEST_FILE = "test_solution.py"
MAX_TURNS = 8
