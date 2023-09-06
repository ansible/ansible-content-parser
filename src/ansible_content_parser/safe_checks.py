"""Check if a given archive (zip/tar) file is safe."""

# Ref: https://sonarcloud.io/organizations/ansible/rules?open=python%3AS5042&rule_key=python%3AS5042&tab=how_to_fix
import tarfile
import zipfile


threshold_entries = 10000
threshold_size = 1000000000
threshold_ratio = 10


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

            total_entry_archive += 1
            size_entry = 0
            while True:
                size_entry += 1024
                total_size_archive += 1024

                ratio = size_entry / entry.size
                # Added the check if entry.size is larger than 1024. When it is very small (like 20 bytes or so)
                # the ratio can exceed the threshold.
                if entry.size > 1024 and ratio > threshold_ratio:
                    msg = "ratio between compressed and uncompressed data is highly suspicious, looks like a Zip Bomb Attack"
                    raise RuntimeError(
                        msg,
                    )

                if tarinfo is None:
                    break
                chunk = tarinfo.read(1024)
                if not chunk:
                    break

            if total_entry_archive > threshold_entries:
                msg = "too much entries in this archive, can lead to inodes exhaustion of the system"
                raise RuntimeError(
                    msg,
                )

            if total_size_archive > threshold_size:
                msg = "the uncompressed data size is too much for the application resource capacity"
                raise RuntimeError(
                    msg,
                )


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
            ratio = len(data) / info.compress_size
            if ratio > threshold_ratio:
                msg = "ratio between compressed and uncompressed data is highly suspicious, looks like a Zip Bomb Attack"
                raise RuntimeError(
                    msg,
                )

            if total_size_archive > threshold_size:
                msg = "the uncompressed data size is too much for the application resource capacity"
                raise RuntimeError(
                    msg,
                )

            if total_entry_archive > threshold_entries:
                msg = "too much entries in this archive, can lead to inodes exhaustion of the system"
                raise RuntimeError(
                    msg,
                )
