import unittest

from unittest.mock import patch, Mock

import tmpfs_framework

tmpfs_framework.TMPFS_PATH = "/tmp/"

from tmpfs_framework import SensorWriter
from tmpfs_framework.sensor_writer import pack_to_zip

class TestSensorWriter(unittest.TestCase):

    @patch('pathlib.Path.mkdir')
    @patch('os.makedirs')
    def test_init_creates_directories(self, mock_makedirs, mock_mkdir):
        sw = SensorWriter("testdir", "testfile")
        mock_makedirs.assert_called_with("/tmp/testdir", exist_ok=True, )
        mock_mkdir.assert_called_with(parents=True,exist_ok=True)

    @patch('os.makedirs')
    @patch('pathlib.Path.mkdir')
    def test_stop_sets_event(self, *args):
        sw = SensorWriter("testdir", "testfile", tmpfs_path="/tmp/")
        sw.stop()
        self.assertTrue(sw.stop_event.is_set())
        #shutil.rmtree("/tmp/testdir", ignore_errors=True)

    @patch('os.makedirs')
    @patch('pathlib.Path.mkdir')
    @patch("tmpfs_framework.sensor_writer.write_cbor")
    def test_write_nested_dict(self, mock_write_cbor, *args):
        sw = SensorWriter("testdir", "testfile")
        data = {"a": {"b": 1, "c":2}}
        sw.write("data", data)
        self.assertEqual(mock_write_cbor.call_count, 2)


    @patch('pathlib.Path.mkdir')
    @patch('os.makedirs')
    @patch("tmpfs_framework.sensor_writer.write_cbor")
    def test_write_with_attributes(self, mock_write_cbor, mock_makedirs, mock_mkdir):
        sw = SensorWriter("testdir", "testfile")
        sw.write("data", 123, attributes={"meta": "info"})
        self.assertEqual(mock_write_cbor.call_count, 2)

    @patch("tmpfs_framework.sensor_writer.get_temp_file", return_value="test")
    @patch('tmpfs_framework.sensor_writer.os')
    @patch('tmpfs_framework.sensor_writer.Path')
    @patch("zipfile.ZipFile")
    #@patch("tmpfs_framework.sensor_writer.os.rename")
    @patch("tmpfs_framework.sensor_writer.write_cbor")
    def test_write_zip_creates_zip(self, mock_write_cbor,mock_ZipFile, mock_path,  mock_os, *args):
        mock_os.path.join = Mock(return_value="ret")
        mock_os.walk = Mock(return_value=(("root","_",("x","y")),))
        mock_ZipFile.return_value.__enter__.return_value =  Mock()

        sw = SensorWriter("testdir", "testfile2")
        sw.write_zip("data", {"x": 1, "a":3}, compress=True, keep=True)
        self.assertEqual(mock_write_cbor.call_count, 2)
        self.assertEqual(mock_ZipFile.return_value.__enter__.return_value.write.call_count, 2)

        mock_os.rename.assert_called_with("test.zip", "ret.zip")
        mock_ZipFile.assert_called_with('test.zip' ,'w' ,compression=8 ,compresslevel=3   )


    @patch("tmpfs_framework.sensor_writer.get_temp_file", return_value="test")
    @patch("zipfile.ZipFile")
    @patch("os.rename")
    def test_pack_to_zip_creates_zip(self, mock_rename, mock_ZipFile, *args):
        pack_to_zip([], base_dir=tmpfs_framework.TMPFS_PATH, zipname="archive")
        mock_rename.assert_called_with("test.zip","/tmp/archive.zip")
        mock_ZipFile.assert_called_with('test.zip' ,'w' ,compression=False ,compresslevel=3   )
        pack_to_zip([], base_dir=tmpfs_framework.TMPFS_PATH, zipname="archive", compress=True)
        mock_ZipFile.assert_called_with('test.zip' ,'w' ,compression=8 ,compresslevel=3   )


if __name__ == "__main__":
    unittest.main()
