"""Check if a given archive (zip/tar) file is safe."""

# Ref: https://sonarcloud.io/organizations/ansible/rules?open=python%3AS5042&rule_key=python%3AS5042&tab=how_to_fix
import tarfile
import zipfile


threshold_entries = 10000
threshold_size = 1000000000

# Increased threshold_ratio from 10 to 100 for reduce false positives.
threshold_ratio = 100


def _check_total_size_and_entries(
    total_entry_archive: int,
    total_size_archive: int,
) -> None:
    if total_entry_archive > threshold_entries:
        msg = "too many entries in this archive, can lead to inodes exhaustion of the system"
        raise RuntimeError(
            msg,
        )
    if total_size_archive > threshold_size:
        msg = "the uncompressed data size is too much for the application resource capacity"
        raise RuntimeError(
            msg,
        )


def check_tar_file_is_safe(source: str) -> None:
    """Make sure that expanding the tar file is safe."""
    if not tarfile.is_tarfile(source):
        msg = f"{source} is not a valid tar archive file."
        raise RuntimeError(
            msg,
        )

    total_size_archive = 0
    total_entry_archive = 0

    with tarfile.open(source) as f:  # NOSONAR
        for entry in f:
            tarinfo = f.extractfile(entry)
            if tarinfo:
                total_entry_archive += 1
                size_entry = 0
                while True:
                    size_entry += 1024
                    total_size_archive += 1024

                    # Commented out following lines because they do not seem to detect highly compressed tar (e.g .tar.gz
                    # files) like the corresponding logic for zip files.  We should be OK because we will check total
                    # size and entries later.

                    # ratio = size_entry / entry.size
                    # if ratio > threshold_ratio:
                    #     msg = "ratio between compressed and uncompressed data is highly suspicious, looks like a Zip Bomb Attack"
                    #     raise RuntimeError(
                    #         msg,
                    #     )

                    chunk = tarinfo.read(1024)
                    if not chunk:
                        break

            _check_total_size_and_entries(total_entry_archive, total_size_archive)


def check_zip_file_is_safe(source: str) -> None:
    """Make sure that expanding the zip file is safe."""
    if not zipfile.is_zipfile(source):
        msg = f"{source} is not a valid zip file."
        raise RuntimeError(
            msg,
        )

    total_size_archive = 0
    total_entry_archive = 0

    with zipfile.ZipFile(source, "r") as f:
        for info in f.infolist():
            data = f.read(info)
            total_entry_archive += 1

            total_size_archive = total_size_archive + len(data)
            ratio = (len(data) / info.compress_size) if info.compress_size != 0 else 1
            if ratio > threshold_ratio:
                msg = "ratio between compressed and uncompressed data is highly suspicious, looks like a Zip Bomb Attack"
                raise RuntimeError(
                    msg,
                )

            _check_total_size_and_entries(total_entry_archive, total_size_archive)
