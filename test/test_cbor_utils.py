import unittest
import numpy as np
import cbor2
import os
from unittest.mock import patch, mock_open, MagicMock

from tmpfs_framework import cbor_utils

class TestCBORUtils(unittest.TestCase):

    def test_decode_homogenous_array(self):
        arr = np.array([1, 2, 3], dtype=np.uint8)
        tag = cbor2.CBORTag(64, arr.tobytes())
        result = cbor_utils._decode_homogenous_arary(None, tag)
        np.testing.assert_array_equal(result, arr)

    def test_decode_tag_40(self):
        arr = np.array([[1, 2], [3, 4]], dtype=np.int32)
        shape = arr.shape
        tag = cbor2.CBORTag(40, [shape, arr.flatten()])
        result = cbor_utils._decode_tag_40(None, tag)
        np.testing.assert_array_equal(result, arr)

    def test_numpy_encoder_1d(self):
        arr = np.array([1, 2, 3], dtype=np.uint8)
        encoder = MagicMock()
        cbor_utils._numpy_encoder(encoder, arr)
        encoder.encode_semantic.assert_called_once()

    def test_numpy_encoder_2d(self):
        arr = np.array([[1, 2], [3, 4]], dtype=np.uint8)
        encoder = MagicMock()
        cbor_utils._numpy_encoder(encoder, arr)
        encoder.encode_semantic.assert_called_once()

    @patch("tmpfs_framework.cbor_utils.get_temp_file", return_value="/tmp/testfile.cbor")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.rename")
    def test_write_cbor(self, mock_rename, mock_open_file, mock_tmpfile):
        data = {"key": "value"}
        filename = "/tmp/output.cbor"
        cbor_utils.write_cbor(filename, data)
        mock_open_file.assert_called_once_with("/tmp/testfile.cbor", 'wb')
        mock_rename.assert_called_once_with("/tmp/testfile.cbor", filename)

    def test_get_temp_file_default(self):
        with patch("tmpfs_framework.TMPFS_PATH", "/tmpfs"):
            path = cbor_utils.get_temp_file()
            self.assertTrue(path.startswith("/tmpfs/tmp"))

    def test_get_temp_file_custom_path(self):
        path = cbor_utils.get_temp_file(tmpfs_path="/custom/tmpfs")
        self.assertTrue(path.startswith("/custom/tmpfs/tmp"))




if __name__ == "__main__":
    unittest.main()
