# import unittest
# from unittest.mock import (
#     MagicMock,
#     Mock,
#     PropertyMock,
#     mock_open,
#     patch,
#     sentinel,
# )

# from src.service import Config, fetch_data, save_result


# class TestService(unittest.TestCase):
#     def test_fetch_data_with_mock(self):
#         api = Mock()
#         api.get.return_value = {"id": 1}

#         result = fetch_data(api)

#         self.assertEqual(result, {"id": 1})
#         api.get.assert_called_once_with("/data")

#     def test_side_effect_and_call_inspection(self):
#         api = Mock(side_effect=ValueError("API down"))

#         with self.assertRaises(ValueError):
#             fetch_data(api)

#         self.assertEqual(api.call_count, 1)

#     @patch("service.Config.timeout", new_callable=PropertyMock)
#     def test_property_mock(self, mock_timeout):
#         mock_timeout.return_value = 5
#         cfg = Config()

#         self.assertEqual(cfg.timeout, 5)

#     @patch("builtins.open", new_callable=mock_open)
#     def test_mock_open(self, mock_file):
#         save_result("out.txt", "hello")

#         mock_file.assert_called_once_with("out.txt", "w")
#         mock_file().write.assert_called_once_with("hello")

#     def test_magicmock_and_sentinel(self):
#         obj = MagicMock()
#         obj.process.return_value = sentinel.RESULT

#         result = obj.process()

#         self.assertIs(result, sentinel.RESULT)
