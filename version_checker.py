import asyncio
import sys
from functools import wraps
from pathlib import Path
import aiohttp

import click


version_file = Path(__file__).parent.joinpath("VERSION")


def get_version() -> tuple[int, int, int]:
    with open(version_file, "r") as version:
        version_str = version.readline()
        version.flush()
    major, minor, patch = tuple(version_str.split("."))
    return int(major), int(minor), int(patch)


def make_version_string(major: int, minor: int, patch: int) -> str:
    return f"{major}.{minor}.{patch}"


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@click.command()
@coro
@click.option('--return-version', is_flag=True, required=False, default=False, help="Return the current version only.")
@click.option('--bump-patch', is_flag=True, required=False, default=False, help="Make a patch version bump.")
@click.option('--bump-minor', is_flag=True, required=False, default=False, help="Make a minor version bump.")
@click.option('--bump-major', is_flag=True, required=False, default=False, help="Make a minor version bump.")
async def check_version(return_version: bool, bump_patch: bool, bump_minor: bool, bump_major: bool):
    major, minor, patch = get_version()
    version_str = make_version_string(major, minor, patch)
    if return_version:
        click.echo(version_str)
        sys.exit(0)
    async with aiohttp.ClientSession() as session:
        async with session.get("http://levan.home:5000/v2/water-bowl-api/tags/list") as resp:
            resp_json = await resp.json()
            available_versions = resp_json.get("tags", [])
    if version_str in available_versions:
        major = major + 1 if bump_major else major
        minor = minor + 1 if bump_minor else minor
        patch = patch + 1 if bump_patch else patch
        new_version_str = make_version_string(major, minor, patch)
        if new_version_str in available_versions:
            click.echo("Version already exists, please update the VERSION file.")
            sys.exit(2)
        with open(version_file, "w") as version:
            click.echo(f"Version bumped from {version_str} to {new_version_str}.")
            version.write(new_version_str)
            version.flush()
            sys.exit(1)
    click.echo("Version ok.")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(check_version())
