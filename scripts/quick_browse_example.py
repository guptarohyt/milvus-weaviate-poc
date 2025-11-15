#!/usr/bin/env python3
"""
Quick non-interactive example showing how to browse database data.
Run this to see what browsing looks like!
"""

from pymilvus import connections, Collection, utility
import weaviate
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

console.print("\n[bold cyan]═══════════════════════════════════════════════════════[/bold cyan]")
console.print("[bold cyan]       QUICK DATABASE BROWSE EXAMPLE[/bold cyan]")
console.print("[bold cyan]═══════════════════════════════════════════════════════[/bold cyan]\n")

# Connect to Milvus
console.print("[yellow]📡 Connecting to Milvus...[/yellow]")
connections.connect(alias="default", host="localhost", port="19530")
console.print("[green]✓ Connected to Milvus[/green]\n")

# List collections
collections = utility.list_collections()
console.print(Panel(f"[bold]Found {len(collections)} collections[/bold]", border_style="blue"))

table = Table(title="Milvus Collections", box=box.ROUNDED)
table.add_column("Collection", style="cyan", no_wrap=True)
table.add_column("Records", style="green", justify="right")

for coll_name in collections:
    coll = Collection(coll_name)
    coll.flush()
    table.add_row(coll_name, str(coll.num_entities))

console.print(table)

# Browse images_phase2 collection
console.print("\n[yellow]📸 Browsing images_phase2 collection...[/yellow]\n")

collection = Collection("images_phase2")
collection.load()

# Get schema
schema = collection.schema
console.print(Panel(
    f"[bold]Collection:[/bold] images_phase2\n"
    f"[bold]Total Records:[/bold] {collection.num_entities}\n"
    f"[bold]Vector Fields:[/bold] image_embedding (512d), text_embedding (384d)",
    title="Collection Info",
    border_style="blue"
))

# Query first 5 records
results = collection.query(
    expr="id != ''",
    output_fields=["id", "filename", "damage_type", "severity", "claim_id"],
    limit=5
)

# Display results
data_table = Table(title="Sample Records", box=box.ROUNDED, show_lines=True)
data_table.add_column("ID", style="cyan")
data_table.add_column("Filename", style="green")
data_table.add_column("Damage Type", style="yellow")
data_table.add_column("Severity", style="red", justify="right")
data_table.add_column("Claim ID", style="magenta")

for record in results:
    data_table.add_row(
        record['id'],
        record['filename'][:30],
        record['damage_type'],
        f"{record['severity']:.2f}",
        record['claim_id']
    )

console.print(data_table)

# Get one record with vectors
console.print("\n[yellow]🔍 Viewing detailed record with vectors...[/yellow]\n")

detailed = collection.query(
    expr=f'id == "{results[0]["id"]}"',
    output_fields=["id", "filename", "damage_type", "severity", "description"],
    limit=1
)

if detailed:
    record = detailed[0]

    console.print(Panel(
        f"[bold cyan]{record['id']}[/bold cyan]\n\n"
        f"[yellow]Filename:[/yellow] {record['filename']}\n"
        f"[yellow]Damage Type:[/yellow] {record['damage_type']}\n"
        f"[yellow]Severity:[/yellow] {record['severity']}\n"
        f"[yellow]Description:[/yellow] {record['description'][:100]}...",
        title="Record Details",
        border_style="green"
    ))

    # Note about vectors (not fetching them for speed)
    console.print("[dim]Note: This record also contains:[/dim]")
    console.print("[dim]  • image_embedding: 512-dimensional CLIP vector[/dim]")
    console.print("[dim]  • text_embedding: 384-dimensional text vector[/dim]")

connections.disconnect(alias="default")

# Now Weaviate
console.print("\n\n[yellow]📡 Connecting to Weaviate...[/yellow]")
client = weaviate.connect_to_local(host="localhost", port=8080)
console.print("[green]✓ Connected to Weaviate[/green]\n")

# Get PDFs collection
collection = client.collections.get("PDFsPhase2")
response = collection.query.fetch_objects(limit=5)

console.print(Panel(
    f"[bold]Collection:[/bold] PDFsPhase2\n"
    f"[bold]Sample Objects:[/bold] {len(response.objects)}",
    title="Weaviate Collection Info",
    border_style="blue"
))

# Display Weaviate objects
weav_table = Table(title="Weaviate PDF Documents", box=box.ROUNDED, show_lines=True)
weav_table.add_column("Doc ID", style="cyan")
weav_table.add_column("Filename", style="green")
weav_table.add_column("Pages", style="yellow", justify="right")
weav_table.add_column("Has Tables", style="magenta")
weav_table.add_column("Preview", style="white")

for obj in response.objects:
    props = obj.properties
    weav_table.add_row(
        props.get('doc_id', 'N/A'),
        props.get('filename', 'N/A')[:30],
        str(props.get('num_pages', 0)),
        "✓" if props.get('has_tables', False) else "✗",
        props.get('text', '')[:50] + "..."
    )

console.print(weav_table)

client.close()

console.print("\n[bold green]✓ Demo Complete![/bold green]")
console.print("\n[bold]To browse interactively, run:[/bold]")
console.print("[cyan]python database_browser.py[/cyan]\n")
