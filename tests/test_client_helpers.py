import uuid
from typing import Any

import pytest

import lakefs_spec.client_helpers as client_helpers
from lakefs_spec import LakeFSFileSystem
from tests.util import RandomFileFactory


def test_create_tag(
    random_file_factory: RandomFileFactory, fs: LakeFSFileSystem, repository: str, temp_branch: str
) -> None:
    random_file = random_file_factory.make()
    lpath = str(random_file)
    rpath = f"{repository}/{temp_branch}/{random_file.name}"
    fs.put(lpath, rpath, precheck=False)
    client_helpers.commit(
        client=fs.client, repository=repository, branch=temp_branch, message="Commit File Factory"
    )
    try:
        tag_name = f"Change_{uuid.uuid4()}"
        client_helpers.create_tag(
            client=fs.client, repository=repository, ref=temp_branch, tag=tag_name
        )

        assert any(
            commit.get("id") == tag_name
            for commit in fs.client.tags_api.list_tags(repository).results
        )
    finally:
        fs.client.tags_api.delete_tag(repository=repository, tag=tag_name)


def test_merge_into_branch(
    random_file_factory: RandomFileFactory,
    fs: LakeFSFileSystem,
    repository: str,
    temp_branch: str,
    temporary_branch_context: Any,
) -> None:
    random_file = random_file_factory.make()

    with temporary_branch_context("merge-into-branch-test") as new_branch:
        source_ref = f"{repository}/{new_branch}/{random_file.name}"
        with fs.scope(create_branch_ok=True):
            fs.put(str(random_file), source_ref)
            client_helpers.commit(
                client=fs.client,
                repository=repository,
                branch=new_branch,
                message="Commit new file",
            )

        assert (
            len(
                fs.client.refs_api.diff_refs(
                    repository=repository, left_ref=temp_branch, right_ref=new_branch
                ).results
            )
            > 0
        )
        client_helpers.merge(
            client=fs.client,
            repository=repository,
            source_ref=new_branch,
            target_branch=temp_branch,
        )
        assert (
            len(
                fs.client.refs_api.diff_refs(
                    repository=repository, left_ref=temp_branch, right_ref=new_branch
                ).results
            )
            == 0
        )


def test_merge_into_branch_aborts_on_no_diff(
    caplog: pytest.LogCaptureFixture, fs: LakeFSFileSystem, repository: str, temp_branch: str
) -> None:
    client_helpers.merge(
        client=fs.client, repository=repository, source_ref="main", target_branch=temp_branch
    )
    assert caplog.records[0].message == "No difference between source and target. Aborting merge."


def test_revert(
    fs: LakeFSFileSystem, random_file_factory: RandomFileFactory, repository: str, temp_branch: str
) -> None:
    random_file = random_file_factory.make()
    source_ref = f"{repository}/{temp_branch}/{random_file.name}"
    with fs.scope(create_branch_ok=True):
        fs.put(str(random_file), source_ref)
        client_helpers.commit(
            client=fs.client, repository=repository, branch=temp_branch, message="Commit new file"
        )
    assert (
        len(
            fs.client.refs_api.diff_refs(
                repository=repository, left_ref="main", right_ref=temp_branch
            ).results
        )
        > 0
    )
    client_helpers.revert(client=fs.client, repository=repository, branch=temp_branch)
    assert (
        len(
            fs.client.refs_api.diff_refs(
                repository=repository, left_ref="main", right_ref=temp_branch
            ).results
        )
        == 0
    )
