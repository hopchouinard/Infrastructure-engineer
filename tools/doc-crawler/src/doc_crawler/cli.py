"""
Command-line interface for the UniFi Documentation Crawler.

Provides commands for:
- Running the crawler with various options
- Checking crawl status and statistics
- Managing cached documentation

TODO: Implement in task F1.8
"""

import click

from doc_crawler import __version__

__all__ = ["main"]


@click.group()
@click.version_option(version=__version__, prog_name="unifi-docs")
def main() -> None:
    """UniFi Documentation Crawler - fetch and organize UniFi docs for offline use."""
    pass


@main.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output directory for crawled documentation",
)
def crawl(_config: str | None, _output: str | None) -> None:
    """Run the documentation crawler."""
    # TODO: Implement in task F1.8
    # _config and _output will be used when implementing the crawler
    click.echo("Crawler not yet implemented. See task F1.8.")


@main.command()
def status() -> None:
    """Show crawl status and statistics."""
    # TODO: Implement in task F1.8
    click.echo("Status command not yet implemented. See task F1.8.")


if __name__ == "__main__":
    main()
