import unittest
import os
import shutil
from unittest.mock import patch, MagicMock
from generate_qr import create_qr_with_logo

class TestGenerateQR(unittest.TestCase):
    def setUp(self):
        self.test_dir = 'test_qrcodes'
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_create_qr_simple(self):
        output_path = os.path.join(self.test_dir, 'test.png')
        url = "https://example.com"
        create_qr_with_logo(url, output_path, logo_path=None)
        
        self.assertTrue(os.path.exists(output_path))
        # Could verify it's a valid image using PIL if needed, but existence is good start.

    @patch('PIL.Image.open')
    def test_create_qr_with_logo(self, mock_open):
        output_path = os.path.join(self.test_dir, 'test_logo.png')
        url = "https://example.com"
        
        # Create a dummy logo file for check existence logic
        logo_path = os.path.join(self.test_dir, 'dummy_logo.png')
        with open(logo_path, 'w') as f:
            f.write('dummy')

        # Mock Image object
        mock_img = MagicMock()
        mock_img.size = (100, 100)
        mock_img.getbands.return_value = ['R', 'G', 'B']
        mock_open.return_value = mock_img

        create_qr_with_logo(url, output_path, logo_path=logo_path)
        
        self.assertTrue(os.path.exists(output_path))

if __name__ == '__main__':
    unittest.main()
