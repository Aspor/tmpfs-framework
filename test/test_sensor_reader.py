import unittest
from unittest.mock import patch, mock_open, Mock


from tmpfs_framework.sensor_reader import SensorReader
from tmpfs_framework.sensor_reader import read, SensorNotInitializedError


class TestSensorReader(unittest.TestCase):


    @patch("os.path.isdir", return_value=True)
    @patch("os.path.isfile", return_value=True)
    @patch("os.stat")
    @patch("os.listdir", return_value=["test", "test.zip", "measurement.zip", "metadata.zip"])
    def test_initialization(self, *args):
        sr = SensorReader("testdir", "testfile")
        self.assertTrue(sr.has_metaFile)
        self.assertTrue(sr.has_zip)
        self.assertEqual(sr.filename, "testfile")
        #sort lists for comparision
        #comparing collections.Counter(list) would be faster but this is more readable
        self.assertEqual(sorted(sr.attributes), sorted(["test", "test_zip","metadata","measurement","attributes" ])  )




    @patch("os.path.isfile", return_value=True)
    @patch("os.path.isdir", return_value=False)
    @patch("os.stat")
    def test_get_metadata_location(self, *args):
        sr = SensorReader("testdir", "testfile", tmpfs_path="/tmpfs")
        location = sr.get_metadata_location()
        self.assertEqual(location,'/tmpfs/testdir/testfile')
        sr.has_metaFile = True
        location = sr.get_metadata_location()
        self.assertEqual(location,'/tmpfs/testdir/testfile/metadata.zip')



    @patch("os.path.isfile", return_value=True)
    @patch("os.path.isdir", return_value=False)
    @patch("os.stat")
    def test_get_packed_data_location(self, *args):
        sr = SensorReader("testdir", "testfile", tmpfs_path="/tmpfs")
        location = sr.get_packed_data_location()
        self.assertTrue(isinstance(location, str))

    @patch("os.path.isfile", return_value=True)
    @patch("os.path.isdir", return_value=False)
    @patch("os.stat")
    @patch("tmpfs_framework.sensor_reader.read")
    def test_get_value(self, mock_read, *args):
        mock_read.return_value = "mocked_data"
        sr = SensorReader("testdir", "testfile", tmpfs_path="/tmpfs")
        value = sr.get_value("testfile")
        self.assertEqual(value, "mocked_data")

    @patch("os.path.isfile", return_value=True)
    @patch("os.path.isdir", return_value=False)
    @patch("os.stat")
    @patch("builtins.open", new_callable=mock_open, read_data=b"binarydata")
    def test_get_binary(self, *args):
        sr = SensorReader("testdir", "testfile", tmpfs_path="/tmpfs")
        result = sr.get_binary("testfile")
        self.assertEqual(result, b"binarydata")

    @patch("os.path.isfile", return_value=True)
    @patch("os.path.isdir", return_value=False)
    @patch("os.stat")
    @patch("tmpfs_framework.sensor_reader.read")
    def test_get_data(self, mock_read, *args):
        mock_read.return_value = ("data", "intrinsics")
        sr = SensorReader("testdir", "testfile", tmpfs_path="/tmpfs")
        data, intrinsics = sr.get_data()
        self.assertEqual(data, "data")
        self.assertEqual(intrinsics, "intrinsics")

    @patch("builtins.open")
    @patch("os.path.isdir", return_value=False)
    @patch("cbor2.CBORDecoder", return_value=Mock())
    def test_read(self, mock_decoder, mock_isdir, mock_open,*args):
        read("test",None)
        mock_open.assert_called_with("test",'rb')
        self.assertEqual(mock_decoder.return_value.decode.call_count,1)

    @patch("os.path.isdir", return_value=False)
    @patch("zipfile.ZipFile")
    @patch("cbor2.CBORDecoder")
    def test_read_zip(self, mock_decoder, mock_ZipFile, *args):
        mock_a =MockZipInfo(filename = "a")
        mock_b =MockZipInfo(filename ="b")
        mock_ZipFile.return_value.__enter__.return_value.infolist = Mock(return_value=[mock_a,mock_b])
        ret = read("test.zip",None)
        self.assertEqual(list(ret.keys()), ["a","b"])
        self.assertEqual(mock_decoder.return_value.decode.call_count,2)

    @patch("os.path.isdir", return_value=False)
    @patch("zipfile.ZipFile")
    @patch("cbor2.CBORDecoder")
    def test_read_zip_recurse(self, mock_decoder, mock_ZipFile, *args):
        a=MockZipInfo(filename ="main/1/a")
        b=MockZipInfo(filename ="main/2/b")
        c=MockZipInfo(filename ="main/1/c")
        mock_ZipFile.return_value.__enter__.return_value.infolist = Mock(
                                return_value=[a,b,c])
        ret = read("test.zip",None)
        self.assertEqual(list(ret.keys()), ["1","2"])
        self.assertEqual(list(ret['1'].keys()), ["a","c"])
        self.assertEqual(mock_decoder.return_value.decode.call_count,3)


    def test_nonexistent_base_dir(self):
        with self.assertRaises( FileNotFoundError):
            SensorReader("testdir", "testfile")

    @patch("os.path.isdir", return_value=True)
    @patch("os.listdir", return_value=[])
    def test_empty_dir_raises_SensorNotInitialized(self, *args):
        with self.assertRaises(SensorNotInitializedError):
            SensorReader("testdir", "testfile")


    def test_read_zip(self, *args):
        import os
        file_path = os.path.realpath(os.path.dirname(__file__))
        zip_test_path = os.path.join(file_path,"test_data/zip_test.zip")
        exepted_result = {"int_arr":[1,2,3],"float_arr":[1.1,2.2,3.3],"float_arr_2":[[1.1,1.2,1.3],[2.1,2.2,2.3]] }
        result = read(zip_test_path)
        self.assertEqual(result["int_arr"], exepted_result["int_arr"])
        self.assertEqual(result["float_arr"], exepted_result["float_arr"])
        self.assertEqual(result["float_arr_2"], exepted_result["float_arr_2"])

    def test_read_zip(self, *args):
        import os
        file_path = os.path.realpath(os.path.dirname(__file__))
        zip_test_path = os.path.join(file_path,"test_data/zip_test_2.zip")
        exepted_result = {"int_arr":[1,2,3],"float_arr":[1.1,2.2,3.3],"float_arr_2":[[1.1,1.2,1.3],[2.1,2.2,2.3]] }
        result = read(zip_test_path)
        self.assertEqual(result["test1"]["int_arr"], exepted_result["int_arr"])
        self.assertEqual(result["test1"]["float_arr"], exepted_result["float_arr"])
        self.assertEqual(result["test2"]["int_arr"], exepted_result["int_arr"])
        self.assertEqual(result["test2"]["float_arr"], exepted_result["float_arr_2"])

class MockZipInfo(Mock):
    def __init__(self, filename="", is_dir= False,  spec = None, side_effect = None, return_value = ..., wraps = None, name = None, spec_set = None, parent = None, _spec_state = None, _new_name = "", _new_parent = None, **kwargs):
        super().__init__(spec, side_effect, return_value, wraps, name, spec_set, parent, _spec_state, _new_name, _new_parent, **kwargs)
        self.filename = filename
        self.is_dir =Mock()
        self.is_dir.return_value = is_dir



if __name__ == "__main__":
    unittest.main()
