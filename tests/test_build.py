import unittest
import os
from unittest.mock import patch, MagicMock
from build import build, TOML_FILE, ENRICHED_TOML_FILE, OUTPUT_FILE

class TestBuild(unittest.TestCase):

    def setUp(self):
        # Create a dummy data.toml
        self.original_toml = TOML_FILE
        self.original_enriched = ENRICHED_TOML_FILE
        self.original_output = OUTPUT_FILE
        
        # We will use the file names from imported module, but in real execution 
        # the test runs in the same dir, so we can just create 'data.toml'.
        # However, to be safe and avoid overwriting user data, we should probably mock the file paths
        # BUT build.py uses global variables for filenames. We can patch them?
        # Since they are imported from build, modifying them here won't change them in build module 
        # unless we patch 'build.TOML_FILE'.
        
        pass

    def tearDown(self):
        # Cleanup is handled in the test via patches or temp files
        pass

    @patch('build.subprocess.run')
    @patch('build.process_data_with_geocoding')
    @patch('build.TOML_FILE', 'test_data.toml')
    @patch('build.ENRICHED_TOML_FILE', 'test_data_enriched.toml')
    @patch('build.OUTPUT_FILE', 'test_index.html')
    @patch('build.OUTPUT_FILE_UNMIN', 'test_index_unminified.html')
    def test_build(self, mock_process, mock_subprocess):
        # Setup test data
        with open('test_data.toml', 'w') as f:
            f.write('title = "Test Site"\n[[businesses]]\nname = "Test Biz"\n')

        try:
            build()
            
            # Check if output files exist
            self.assertTrue(os.path.exists('test_data_enriched.toml'))
            self.assertTrue(os.path.exists('test_index.html'))
            self.assertTrue(os.path.exists('test_index_unminified.html'))
            
            # Check content of generated HTML
            with open('test_index.html', 'r') as f:
                content = f.read()
                self.assertIn('<title>Test Site</title>', content)
                self.assertIn('Test Biz', content)
            
            # Check unminified
            with open('test_index_unminified.html', 'r') as f:
                content = f.read()
                self.assertIn('<title>Test Site</title>', content)
                
            mock_process.assert_called()

            # Validate generated HTML files are valid
            from tidylib import tidy_document
            tidy_options = {
                'show-warnings': 0,
                'new-blocklevel-tags': 'header,nav,section,article,aside,footer,main',
            }
            for html_file in ['test_index.html', 'test_index_unminified.html']:
                with open(html_file, 'r') as f:
                    html_content = f.read()
                _, errors = tidy_document(html_content, options=tidy_options)
                self.assertEqual(errors, '', f"HTML validation errors in {html_file}: {errors}")

        finally:
            # Cleanup
            for f in ['test_data.toml', 'test_data_enriched.toml', 'test_index.html', 'test_index_unminified.html']:
                if os.path.exists(f):
                    os.remove(f)

if __name__ == '__main__':
    unittest.main()
