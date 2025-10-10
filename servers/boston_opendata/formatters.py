from typing import Any, Dict, Optional


def format_dataset_summary(dataset: Dict[str, Any], index: Optional[int] = None) -> str:
    prefix = f"{index}. " if index else ""
    title = dataset.get("title", "Untitled Dataset")
    name = dataset.get("name", "N/A")
    notes = dataset.get("notes", "No description available")

    if len(notes) > 200:
        notes = notes[:200] + "..."

    notes = " ".join(notes.split())
    num_resources = len(dataset.get("resources", []))

    output = f"{prefix}**{title}**\n"
    output += f"   📝 {notes}\n"
    output += f"   🆔 ID: `{name}`\n"
    output += f"   📊 Resources: {num_resources}\n"
    output += f"   🔗 https://data.boston.gov/dataset/{name}\n"
    return output


def format_resource_info(resource: Dict[str, Any], index: Optional[int] = None) -> str:
    prefix = f"{index}. " if index else ""
    name = resource.get("name", "Unnamed Resource")
    res_id = resource.get("id", "N/A")
    fmt = resource.get("format", "Unknown")
    desc = resource.get("description", "")
    has_datastore = resource.get("datastore_active", False)

    output = f"{prefix}{name}\n"
    output += f"   🆔 Resource ID: `{res_id}`\n"
    output += f"   📄 Format: {fmt}\n"
    output += f"   🗄️  DataStore: {'✅ Yes (Queryable)' if has_datastore else '❌ No'}\n"

    if desc:
        desc_short = desc[:100] + "..." if len(desc) > 100 else desc
        output += f"   📝 {desc_short}\n"

    return output

