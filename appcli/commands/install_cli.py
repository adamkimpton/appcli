#!/usr/bin/env python3
# # -*- coding: utf-8 -*-

"""
The install command available when running the CLI.

Responsible for installing the application to the host system.

NOTE: This script makes hard assumptions about the location of files. It MUST
      be run within a container.
________________________________________________________________________________

Created by brightSPARK Labs
www.brightsparklabs.com
"""

# standard library
import datetime
import importlib.resources as pkg_resources
import os
from pathlib import Path

# vendor libraries
import click
from jinja2 import StrictUndefined, Template

# local libraries
from appcli import templates
from appcli.functions import error_and_exit
from appcli.logger import logger
from appcli.models.cli_context import CliContext
from appcli.models.configuration import Configuration

# ------------------------------------------------------------------------------
# CONSTANTS
# ------------------------------------------------------------------------------

INSTALLER_TEMPLATE_FILENAME = "installer.j2"
""" The filename of the installer template """

# ------------------------------------------------------------------------------
# CLASSES
# ------------------------------------------------------------------------------


class InstallCli:

    # ------------------------------------------------------------------------------
    # CONSTRUCTOR
    # ------------------------------------------------------------------------------

    def __init__(self, configuration: Configuration):
        self.configuration: Configuration = configuration
        default_install_dir = f"/opt/brightsparklabs/{configuration.app_name.lower()}"

        @click.command(
            hidden=True, help="Outputs an appropriate installer bash script to stdout."
        )
        @click.option(
            "--install-dir",
            "-i",
            help="Directory to install into. Defaults to '{default_install_dir}/<ENVIRONMENT>'.",
            type=Path,
            default=default_install_dir,
        )
        @click.pass_context
        # NOTE: Hide the cli command as end users should not run it manually
        def install(ctx, install_dir: Path):
            logger.info("Generating installer script ...")

            # Get the template from the appcli package
            launcher_template = pkg_resources.read_text(
                templates, INSTALLER_TEMPLATE_FILENAME
            )
            logger.debug(f"Read template file [{INSTALLER_TEMPLATE_FILENAME}]")

            cli_context: CliContext = ctx.obj
            environment: str = cli_context.environment
            target_install_dir: Path = install_dir / environment
            if cli_context.configuration_dir is None:
                cli_context = cli_context._replace(
                    configuration_dir=target_install_dir / "conf"
                )
            if cli_context.data_dir is None:
                cli_context = cli_context._replace(data_dir=target_install_dir / "data")

            render_variables = {
                "cli_context": cli_context,
                "configuration": self.configuration,
                "install_dir": f"{install_dir}/{environment}",
            }

            logger.debug(
                f"Rendering template with render variables: [{render_variables}]"
            )

            template = Template(
                launcher_template,
                undefined=StrictUndefined,
                trim_blocks=True,
                lstrip_blocks=True,
            )
            try:
                output_text = template.render(render_variables)
                print(output_text)
            except Exception as e:
                error_and_exit(
                    f"Could not generate file from template. The configuration file is likely missing a setting: {e}"
                )

        # expose the cli command
        self.commands = {"install": install}
