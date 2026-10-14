#!/usr/bin/env python3
"""Read-only GCP networking preview and verification."""

import argparse
import json
import os
import sys
from pathlib import Path

import google.auth
import yaml
from google.auth.transport.requests import AuthorizedSession


def load_config():
    config_path = Path(
        os.environ.get(
            "CONFIG_FILE",
            "inventories/dev/group_vars/all.yml",
        )
    )

    with config_path.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    if not isinstance(config, dict):
        raise ValueError("Environment configuration must be a mapping")

    if not config.get("gcp_project"):
        raise ValueError("Missing gcp_project")

    network = config.get("network", {})
    if not network.get("name"):
        raise ValueError("Missing network.name")

    subnets = config.get("subnets", [])
    if not isinstance(subnets, list) or not subnets:
        raise ValueError("At least one subnet must be configured")

    return config


def get_resource(session, url):
    response = session.get(url, timeout=30)

    if response.status_code == 404:
        return None

    response.raise_for_status()
    return response.json()


def compare_resource(name, current, expected):
    if current is None:
        return {
            "resource": name,
            "action": "CREATE",
            "differences": {},
        }

    differences = {}

    for field, desired_value in expected.items():
        actual_value = current.get(field)

        if actual_value != desired_value:
            differences[field] = {
                "actual": actual_value,
                "expected": desired_value,
            }

    return {
        "resource": name,
        "action": "DRIFT" if differences else "NO_CHANGE",
        "differences": differences,
    }


def collect_network_state(session, config):
    project = config["gcp_project"]
    network = config["network"]

    base_url = (
        "https://compute.googleapis.com/compute/v1/"
        f"projects/{project}"
    )

    vpc_name = network["name"]

    vpc = get_resource(
        session,
        f"{base_url}/global/networks/{vpc_name}",
    )

    vpc_expected = {
        "name": vpc_name,
        "autoCreateSubnetworks": network[
            "auto_create_subnetworks"
        ],
    }

    if vpc is not None:
        vpc = dict(vpc)
        vpc["routingMode"] = vpc.get(
            "routingConfig", {}
        ).get("routingMode")

    vpc_expected["routingMode"] = network["routing_mode"]

    results = [
        compare_resource(
            f"vpc/{vpc_name}",
            vpc,
            vpc_expected,
        )
    ]

    for subnet in config["subnets"]:
        region = subnet.get(
            "region",
            config.get("gcp_region"),
        )

        if not region:
            raise ValueError("Subnet region is missing")

        subnet_name = subnet["name"]

        current = get_resource(
            session,
            (
                f"{base_url}/regions/{region}/"
                f"subnetworks/{subnet_name}"
            ),
        )

        expected = {
            "name": subnet_name,
            "ipCidrRange": subnet["cidr"],
            "privateIpGoogleAccess": subnet[
                "private_google_access"
            ],
        }

        if current is not None:
            current = dict(current)
            current["networkName"] = current.get(
                "network", ""
            ).rsplit("/", 1)[-1]

        expected["networkName"] = vpc_name

        results.append(
            compare_resource(
                f"subnet/{region}/{subnet_name}",
                current,
                expected,
            )
        )

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=["preview", "verify"],
    )
    args = parser.parse_args()

    config = load_config()

    credentials, _ = google.auth.default(
        scopes=[
            "https://www.googleapis.com/auth/cloud-platform"
        ]
    )

    session = AuthorizedSession(credentials)

    results = collect_network_state(session, config)

    print(f"GCP project: {config['gcp_project']}")
    print(f"Mode: {args.mode}")

    for result in results:
        print(
            f"{result['action']:10} {result['resource']}"
        )

        if result["differences"]:
            print(
                json.dumps(
                    result["differences"],
                    indent=2,
                )
            )

    if args.mode == "preview":
        report = {
            "project": config["gcp_project"],
            "mode": args.mode,
            "resources": results,
        }

        Path("network-plan.json").write_text(
            json.dumps(report, indent=2) + "\n",
            encoding="utf-8",
        )

        if any(
            item["action"] == "DRIFT"
            for item in results
        ):
            print("FAILED: Existing configuration drift detected")
            return 1

        print("Preview completed successfully")
        return 0

    failures = [
        item for item in results
        if item["action"] != "NO_CHANGE"
    ]

    if failures:
        print("FAILED: Infrastructure verification failed")
        return 1

    print("SUCCESS: All networking resources verified")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
