"""
Interactive Database Browser - View data stored in Milvus and Weaviate.
Browse collections, view records, inspect vectors, and search data.
"""

import json
from typing import List, Dict, Any
from pymilvus import connections, Collection, utility
import weaviate
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich import box


class DatabaseBrowser:
    """Interactive browser for Milvus and Weaviate databases."""

    def __init__(self):
        """Initialize browser."""
        self.console = Console()
        self.milvus_connected = False
        self.weaviate_connected = False
        self.weaviate_client = None

    def connect_milvus(self):
        """Connect to Milvus."""
        try:
            connections.connect(alias="default", host="localhost", port="19530")
            self.milvus_connected = True
            self.console.print("[green]✓ Connected to Milvus[/green]")
            return True
        except Exception as e:
            self.console.print(f"[red]✗ Failed to connect to Milvus: {e}[/red]")
            return False

    def connect_weaviate(self):
        """Connect to Weaviate."""
        try:
            self.weaviate_client = weaviate.connect_to_local(host="localhost", port=8080)
            self.weaviate_connected = True
            self.console.print("[green]✓ Connected to Weaviate[/green]")
            return True
        except Exception as e:
            self.console.print(f"[red]✗ Failed to connect to Weaviate: {e}[/red]")
            return False

    def list_milvus_collections(self):
        """List all Milvus collections."""
        if not self.milvus_connected:
            if not self.connect_milvus():
                return

        collections = utility.list_collections()

        if not collections:
            self.console.print("[yellow]No collections found in Milvus[/yellow]")
            return

        table = Table(title="Milvus Collections", box=box.ROUNDED)
        table.add_column("Collection Name", style="cyan")
        table.add_column("# Entities", style="green", justify="right")

        for coll_name in collections:
            coll = Collection(coll_name)
            coll.flush()
            table.add_row(coll_name, str(coll.num_entities))

        self.console.print(table)

    def list_weaviate_collections(self):
        """List all Weaviate collections."""
        if not self.weaviate_connected:
            if not self.connect_weaviate():
                return

        try:
            collections = self.weaviate_client.collections.list_all()

            if not collections:
                self.console.print("[yellow]No collections found in Weaviate[/yellow]")
                return

            table = Table(title="Weaviate Collections", box=box.ROUNDED)
            table.add_column("Collection Name", style="cyan")
            table.add_column("# Objects", style="green", justify="right")

            for name, config in collections.items():
                try:
                    collection = self.weaviate_client.collections.get(name)
                    agg = collection.aggregate.over_all()
                    count = agg.total_count
                    table.add_row(name, str(count))
                except:
                    table.add_row(name, "N/A")

            self.console.print(table)
        except Exception as e:
            self.console.print(f"[red]Error listing collections: {e}[/red]")

    def browse_milvus_collection(self, collection_name: str, limit: int = 10):
        """Browse data in a Milvus collection."""
        if not self.milvus_connected:
            if not self.connect_milvus():
                return

        try:
            collection = Collection(collection_name)
            collection.load()

            # Get schema info
            schema = collection.schema
            field_names = [field.name for field in schema.fields]

            self.console.print(Panel(
                f"[bold]Collection:[/bold] {collection_name}\n"
                f"[bold]Total Entities:[/bold] {collection.num_entities}\n"
                f"[bold]Fields:[/bold] {', '.join(field_names)}",
                title="Collection Info",
                border_style="blue"
            ))

            # Query data
            output_fields = [f.name for f in schema.fields if not f.name.endswith('embedding')]

            results = collection.query(
                expr="id != ''",
                output_fields=output_fields[:10],  # Limit fields
                limit=limit
            )

            if not results:
                self.console.print("[yellow]No data found[/yellow]")
                return

            # Create table
            table = Table(title=f"First {limit} Records", box=box.ROUNDED)
            for field in output_fields[:10]:
                table.add_column(field, style="cyan", max_width=30)

            for entity in results:
                row = []
                for field in output_fields[:10]:
                    value = entity.get(field, "")
                    # Truncate long strings
                    value_str = str(value)
                    if len(value_str) > 50:
                        value_str = value_str[:47] + "..."
                    row.append(value_str)
                table.add_row(*row)

            self.console.print(table)

            # Ask if user wants to see a specific record
            if Prompt.ask("\nView details of a specific record?", choices=["y", "n"], default="n") == "y":
                record_id = Prompt.ask("Enter record ID")
                self.view_milvus_record(collection_name, record_id)

        except Exception as e:
            self.console.print(f"[red]Error browsing collection: {e}[/red]")

    def view_milvus_record(self, collection_name: str, record_id: str):
        """View a specific record in detail."""
        try:
            collection = Collection(collection_name)
            collection.load()

            schema = collection.schema
            output_fields = [f.name for f in schema.fields]

            results = collection.query(
                expr=f'id == "{record_id}"',
                output_fields=output_fields,
                limit=1
            )

            if not results:
                self.console.print(f"[red]Record {record_id} not found[/red]")
                return

            record = results[0]

            # Display all fields
            self.console.print(Panel(
                f"[bold cyan]Record Details: {record_id}[/bold cyan]",
                border_style="green"
            ))

            for key, value in record.items():
                if 'embedding' in key.lower():
                    # Show embedding info without displaying full vector
                    if isinstance(value, list):
                        self.console.print(f"[yellow]{key}:[/yellow] Vector with {len(value)} dimensions")
                        self.console.print(f"  First 5 values: {value[:5]}")
                        self.console.print(f"  Last 5 values: {value[-5:]}")
                else:
                    value_str = str(value)
                    if len(value_str) > 200:
                        value_str = value_str[:200] + "..."
                    self.console.print(f"[yellow]{key}:[/yellow] {value_str}")

        except Exception as e:
            self.console.print(f"[red]Error viewing record: {e}[/red]")

    def browse_weaviate_collection(self, collection_name: str, limit: int = 10):
        """Browse data in a Weaviate collection."""
        if not self.weaviate_connected:
            if not self.connect_weaviate():
                return

        try:
            collection = self.weaviate_client.collections.get(collection_name)

            # Get collection info
            agg = collection.aggregate.over_all()
            total_count = agg.total_count

            self.console.print(Panel(
                f"[bold]Collection:[/bold] {collection_name}\n"
                f"[bold]Total Objects:[/bold] {total_count}",
                title="Collection Info",
                border_style="blue"
            ))

            # Fetch objects
            response = collection.query.fetch_objects(limit=limit)

            if not response.objects:
                self.console.print("[yellow]No data found[/yellow]")
                return

            # Get property names from first object
            first_obj = response.objects[0]
            property_names = list(first_obj.properties.keys())

            # Create table
            table = Table(title=f"First {limit} Objects", box=box.ROUNDED)
            table.add_column("UUID", style="cyan", max_width=20)
            for prop in property_names[:8]:  # Limit columns
                table.add_column(prop, style="green", max_width=30)

            for obj in response.objects:
                row = [str(obj.uuid)[:16] + "..."]
                for prop in property_names[:8]:
                    value = obj.properties.get(prop, "")
                    value_str = str(value)
                    if len(value_str) > 50:
                        value_str = value_str[:47] + "..."
                    row.append(value_str)
                table.add_row(*row)

            self.console.print(table)

            # Ask if user wants to see a specific record
            if Prompt.ask("\nView details of a specific object?", choices=["y", "n"], default="n") == "y":
                obj_uuid = Prompt.ask("Enter object UUID (or just first 8+ chars)")
                self.view_weaviate_object(collection_name, obj_uuid)

        except Exception as e:
            self.console.print(f"[red]Error browsing collection: {e}[/red]")

    def view_weaviate_object(self, collection_name: str, obj_uuid: str):
        """View a specific Weaviate object in detail."""
        try:
            collection = self.weaviate_client.collections.get(collection_name)

            # Try to find object (handle partial UUID)
            response = collection.query.fetch_objects(limit=100, include_vector=True)

            matching_obj = None
            for obj in response.objects:
                if str(obj.uuid).startswith(obj_uuid):
                    matching_obj = obj
                    break

            if not matching_obj:
                self.console.print(f"[red]Object {obj_uuid} not found[/red]")
                return

            # Display all properties
            self.console.print(Panel(
                f"[bold cyan]Object Details: {matching_obj.uuid}[/bold cyan]",
                border_style="green"
            ))

            # Properties
            for key, value in matching_obj.properties.items():
                value_str = str(value)
                if len(value_str) > 200:
                    value_str = value_str[:200] + "..."
                self.console.print(f"[yellow]{key}:[/yellow] {value_str}")

            # Vectors
            if matching_obj.vector:
                if isinstance(matching_obj.vector, dict):
                    # Named vectors
                    for vector_name, vector_data in matching_obj.vector.items():
                        self.console.print(f"\n[yellow]{vector_name}:[/yellow] Vector with {len(vector_data)} dimensions")
                        self.console.print(f"  First 5 values: {vector_data[:5]}")
                        self.console.print(f"  Last 5 values: {vector_data[-5:]}")
                else:
                    # Single vector
                    self.console.print(f"\n[yellow]Vector:[/yellow] {len(matching_obj.vector)} dimensions")
                    self.console.print(f"  First 5 values: {matching_obj.vector[:5]}")
                    self.console.print(f"  Last 5 values: {matching_obj.vector[-5:]}")

        except Exception as e:
            self.console.print(f"[red]Error viewing object: {e}[/red]")

    def interactive_menu(self):
        """Main interactive menu."""
        self.console.clear()
        self.console.print(Panel(
            "[bold cyan]Database Browser[/bold cyan]\n"
            "View and explore data in Milvus and Weaviate",
            border_style="blue"
        ))

        while True:
            self.console.print("\n[bold]Main Menu:[/bold]")
            self.console.print("1. List Milvus collections")
            self.console.print("2. List Weaviate collections")
            self.console.print("3. Browse Milvus collection")
            self.console.print("4. Browse Weaviate collection")
            self.console.print("5. Exit")

            choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5"], default="5")

            if choice == "1":
                self.list_milvus_collections()
            elif choice == "2":
                self.list_weaviate_collections()
            elif choice == "3":
                if not self.milvus_connected:
                    self.connect_milvus()
                collection_name = Prompt.ask("Enter collection name")
                limit = IntPrompt.ask("How many records to show?", default=10)
                self.browse_milvus_collection(collection_name, limit)
            elif choice == "4":
                if not self.weaviate_connected:
                    self.connect_weaviate()
                collection_name = Prompt.ask("Enter collection name")
                limit = IntPrompt.ask("How many objects to show?", default=10)
                self.browse_weaviate_collection(collection_name, limit)
            elif choice == "5":
                self.console.print("[yellow]Goodbye![/yellow]")
                if self.weaviate_connected:
                    self.weaviate_client.close()
                if self.milvus_connected:
                    connections.disconnect(alias="default")
                break


def main():
    """Main entry point."""
    browser = DatabaseBrowser()

    try:
        browser.interactive_menu()
    except KeyboardInterrupt:
        browser.console.print("\n[yellow]Interrupted by user[/yellow]")
        if browser.weaviate_connected:
            browser.weaviate_client.close()
        if browser.milvus_connected:
            connections.disconnect(alias="default")


if __name__ == "__main__":
    main()
