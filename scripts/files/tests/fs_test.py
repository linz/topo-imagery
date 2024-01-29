# import json

# from boto3 import resource
# from moto import mock_s3
# from moto.s3.responses import DEFAULT_REGION_NAME
# from pytest import CaptureFixture, raises

# from scripts.files.fs import NoSuchFileError, read, write_all, write_sidecars


# def test_read_key_not_found_local() -> None:
#     with raises(NoSuchFileError):
#         read("test_dir/test.file")


# @mock_s3  # type: ignore
# def test_read_key_not_found_s3(capsys: CaptureFixture[str]) -> None:
#     s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
#     s3.create_bucket(Bucket="testbucket")

#     with raises(NoSuchFileError):
#         read("s3://testbucket/test.file")

#     logs = json.loads(capsys.readouterr().out)
#     assert logs["msg"] == "s3_key_not_found"


# def test_write_all_file_not_found_local() -> None:
#     with raises(NoSuchFileError):
#         write_all(["/test.prj"], "/tmp")


# def test_write_sidecars_file_not_found_local(capsys: CaptureFixture[str]) -> None:
#     write_sidecars(["/test.prj"], "/tmp")

#     logs = json.loads(capsys.readouterr().out.strip())
#     assert logs["msg"] == "No sidecar file found; skipping"


# @mock_s3  # type: ignore
# def test_write_all_key_not_found_s3() -> None:
#     s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
#     s3.create_bucket(Bucket="testbucket")

#     with raises(NoSuchFileError):
#         write_all(["s3://testbucket/test.tif"], "/tmp")


# @mock_s3  # type: ignore
# def test_write_sidecars_key_not_found_s3(capsys: CaptureFixture[str]) -> None:
#     s3 = resource("s3", region_name=DEFAULT_REGION_NAME)
#     s3.create_bucket(Bucket="testbucket")

#     write_sidecars(["s3://testbucket/test.prj"], "/tmp")

#     # capsys.readouterr().out json string format is not valid which implies
#     # we can't parse it to find the actual `msg`
#     assert "No sidecar file found; skipping" in capsys.readouterr().out
