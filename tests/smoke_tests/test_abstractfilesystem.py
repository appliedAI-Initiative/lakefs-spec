from lakefs_spec.spec import LakeFSFileSystem


def test_walk_single_dir(fs: LakeFSFileSystem, repository: str) -> None:
    """`walk` in a single directory should find all files contained therein"""
    branch = "main"
    resource = "images"
    path = f"{repository}/{branch}/{resource}/"

    dirname, dirs, files = next(fs.walk(path))
    assert dirname == path
    assert dirs == []
    assert len(files) == 37  # NOTE: hardcoded for quickstart repo


def test_walk_repo_root(fs: LakeFSFileSystem, repository: str) -> None:
    """`walk` should be able to be called on the root directory of a repository"""
    branch = "main"
    path = f"{repository}/{branch}/"

    dirname, dirs, files = next(fs.walk(path))
    assert dirname == path
    assert len(dirs) == 2
    assert len(files) == 2


def test_find_in_folder(fs: LakeFSFileSystem, repository: str) -> None:
    path = f"{repository}/main/"
    # Find the 37 elements in images directory in test repo
    assert len(fs.find(path + "images")) == 37


def test_touch(
    fs: LakeFSFileSystem,
    repository: str,
    temp_branch: str,
) -> None:
    rpath = f"{repository}/{temp_branch}/hello.txt"
    fs.touch(rpath)
    assert fs.exists(rpath)


def test_glob(
    fs: LakeFSFileSystem,
    repository: str,
) -> None:
    branch = "main"
    files = fs.glob(f"lakefs://{repository}/{branch}/**/*.png")
    assert len(files) > 0


def test_du(
    fs: LakeFSFileSystem,
    repository: str,
) -> None:
    branch = "main"
    size = fs.du(f"lakefs://{repository}/{branch}/", withdirs=True)
    assert size > 2**20  # at least 1 MiB in the quickstart repo


def test_size(
    fs: LakeFSFileSystem,
    repository: str,
) -> None:
    branch = "main"
    size = fs.size(f"lakefs://{repository}/{branch}/lakes.parquet")
    assert size >= 2**19  # lakes.parquet is larger than 500 KiB


def test_isfile_isdir(
    fs: LakeFSFileSystem,
    repository: str,
) -> None:
    branch = "main"
    assert fs.isfile(f"lakefs://{repository}/{branch}/lakes.parquet")
    assert not fs.isdir(f"lakefs://{repository}/{branch}/lakes.parquet")

    assert not fs.isfile(f"lakefs://{repository}/{branch}/data")
    assert fs.isdir(f"lakefs://{repository}/{branch}/data")


def test_write_text_read_text(
    fs: LakeFSFileSystem,
    repository: str,
    temp_branch: str,
) -> None:
    rpath = f"lakefs://{repository}/{temp_branch}/new-file.txt"
    content = "Hello, World!"
    encoding = "utf-32-le"  # use a non-standard encoding

    fs.write_text(rpath, content, encoding=encoding)
    actual = fs.read_text(rpath, encoding=encoding)
    assert actual == content


def test_cat_pipe(
    fs: LakeFSFileSystem,
    repository: str,
    temp_branch: str,
) -> None:
    rpath = f"lakefs://{repository}/{temp_branch}/new-file.txt"
    content = "Hello, World!"
    encoding = "utf-32-le"  # use a non-standard encoding
    fs.pipe(rpath, content.encode(encoding))

    actual = fs.cat(rpath)
    assert str(actual, encoding=encoding) == content

    actual = fs.cat_file(rpath, end=4)  # Only fetch first UTF-32 glyph
    assert str(actual, encoding=encoding) == content[0]


def test_cat_pipe_file(
    fs: LakeFSFileSystem,
    repository: str,
    temp_branch: str,
) -> None:
    rpath = f"lakefs://{repository}/{temp_branch}/new-file.txt"
    content = "Hello, World!"
    encoding = "utf-32-le"  # use a non-standard encoding
    fs.pipe_file(rpath, content.encode(encoding))

    actual = fs.cat(rpath)
    assert str(actual, encoding=encoding) == content


def test_cat_ranges(
    fs: LakeFSFileSystem,
    repository: str,
    temp_branch: str,
) -> None:
    rpaths = [f"lakefs://{repository}/{temp_branch}/file-{idx}.txt" for idx in range(2)]
    content = "Hello, World!"
    encoding = "utf8"

    fs.write_text(rpaths[0], content, encoding=encoding)
    fs.write_text(rpaths[1], content, encoding=encoding)

    ranges = fs.cat_ranges(rpaths, starts=0, ends=1)  # fetch first byte of each file
    for idx in range(2):
        assert str(ranges[idx], encoding=encoding) == content[0]


def test_head_tail(
    fs: LakeFSFileSystem,
    repository: str,
    temp_branch: str,
) -> None:
    rpath = f"lakefs://{repository}/{temp_branch}/new-file.txt"
    content = "Hello, World!"
    encoding = "utf-8"

    fs.write_text(rpath, content, encoding=encoding)

    size = 2
    head = fs.head(rpath, size=size)
    assert str(head, encoding=encoding) == content[:size]

    tail = fs.tail(rpath, size=size)
    assert str(tail, encoding=encoding) == content[len(content) - size :]
