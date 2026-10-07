# -*- coding: utf-8 -*-
"""Linked Element ID - Pick a linked element and retrieve its ID.

Allows the user to click an element inside a Revit linked model
and retrieves the ElementId of that element inside the linked document.
The linked Element ID is automatically copied to the clipboard.
"""

__title__ = "Linked\nElement ID"
__author__ = "BIM Tools"
__doc__ = "Pick an element from a linked model to get its Element ID."

# =============================================================================
# CONFIGURATION
# =============================================================================

DEBUG = False

# =============================================================================
# IMPORTS
# =============================================================================

import clr

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

from Autodesk.Revit.DB import (
    RevitLinkInstance,
    ElementId,
    WorksetId,
)
from Autodesk.Revit.UI.Selection import (
    ObjectType,
    ISelectionFilter,
)
from Autodesk.Revit.Exceptions import OperationCanceledException

from pyrevit import script

# =============================================================================
# GLOBALS
# =============================================================================

uidoc = __revit__.ActiveUIDocument  # noqa: F821
doc = uidoc.Document
output = script.get_output()

# =============================================================================
# SELECTION FILTER
# =============================================================================


class LinkedElementSelectionFilter(ISelectionFilter):
    """Selection filter that only allows picking elements inside Revit links.

    AllowElement is called with the host-side element (the RevitLinkInstance).
    AllowReference is called with the Reference to the linked element.
    """

    def AllowElement(self, element):
        """Allow only RevitLinkInstance elements."""
        return isinstance(element, RevitLinkInstance)

    def AllowReference(self, reference, position):
        """Allow the linked element reference."""
        return True


# =============================================================================
# CLIPBOARD HELPER
# =============================================================================


def copy_to_clipboard(text):
    """Copy text to Windows clipboard.

    Uses .NET System.Windows.Forms.Clipboard available in IronPython.
    Returns True on success, False on failure.
    Failure does NOT raise an exception.
    """
    try:
        clr.AddReference("System.Windows.Forms")
        from System.Windows.Forms import Clipboard
        Clipboard.SetText(str(text))
        return True
    except Exception:
        return False


# =============================================================================
# ELEMENT INFO HELPERS
# =============================================================================


def get_element_name(element):
    """Safely retrieve a display name for the element."""
    try:
        # Try the Name property first
        name = element.Name
        if name:
            return name
    except Exception:
        pass

    try:
        # Fall back to element type name
        elem_type = element.Document.GetElement(element.GetTypeId())
        if elem_type:
            type_name = elem_type.Name
            if type_name:
                return type_name
    except Exception:
        pass

    return "Unknown"


def get_element_category(element):
    """Safely retrieve the category name of the element."""
    try:
        if element.Category and element.Category.Name:
            return element.Category.Name
    except Exception:
        pass
    return "Unknown"


def get_element_workset(element, linked_doc):
    """Safely retrieve the workset name of the element."""
    try:
        if linked_doc.IsWorkshared:
            workset_id = element.WorksetId
            if workset_id != WorksetId.InvalidWorksetId:
                workset_table = linked_doc.GetWorksetTable()
                workset = workset_table.GetWorkset(workset_id)
                if workset:
                    return workset.Name
    except Exception:
        pass
    return "Non-Workshared / Unknown"


def get_linked_doc_name(linked_doc):
    """Safely retrieve the linked document title."""
    try:
        title = linked_doc.Title
        if title:
            return title
    except Exception:
        pass
    return "Unknown"


# =============================================================================
# DEBUG HELPER
# =============================================================================


def print_debug(reference, link_instance, linked_doc, linked_element):
    """Print detailed debug information to the output window."""
    if not DEBUG:
        return

    print("=" * 50)
    print("DEBUG INFORMATION")
    print("=" * 50)
    print("Reference:               {}".format(reference))
    print("Reference.ElementId:     {}".format(reference.ElementId))
    print("Reference.LinkedElementId: {}".format(reference.LinkedElementId))

    if link_instance:
        print("RevitLinkInstance ID:    {}".format(link_instance.Id))
        print("RevitLinkInstance Name:  {}".format(link_instance.Name))

    if linked_doc:
        print("Linked document:        {}".format(linked_doc.Title))

    if linked_element:
        print("Linked element ID:      {}".format(linked_element.Id))
        print("Linked element category: {}".format(
            get_element_category(linked_element)
        ))
        print("Linked element name:    {}".format(
            get_element_name(linked_element)
        ))
        print("Linked element workset: {}".format(
            get_element_workset(linked_element, linked_doc)
        ))

    print("=" * 50)


# =============================================================================
# MAIN
# =============================================================================


def main():
    """Main entry point for the Linked Element ID tool."""

    # --- Pick the linked element ---
    try:
        sel_filter = LinkedElementSelectionFilter()
        reference = uidoc.Selection.PickObject(
            ObjectType.LinkedElement,
            sel_filter,
            "Pick an element from a linked model..."
        )
    except OperationCanceledException:
        print("Selection cancelled.")
        return
    except Exception as e:
        print("Selection error: {}".format(e))
        return

    # --- Validate LinkedElementId ---
    linked_element_id = reference.LinkedElementId

    if linked_element_id is None or linked_element_id == ElementId.InvalidElementId:
        print("Could not retrieve the linked element ID.")
        return

    # --- Get the RevitLinkInstance from the host document ---
    link_instance_id = reference.ElementId
    link_instance = doc.GetElement(link_instance_id)

    if not isinstance(link_instance, RevitLinkInstance):
        print("Please select an element from a Revit linked model.")
        return

    # --- Get the linked document ---
    linked_doc = link_instance.GetLinkDocument()

    if linked_doc is None:
        print("The linked model is unavailable or unloaded.")
        return

    # --- Get the linked element ---
    linked_element = linked_doc.GetElement(linked_element_id)

    if linked_element is None:
        print("The linked element could not be retrieved "
              "from the linked document.")
        return

    # --- Gather display information ---
    element_name = get_element_name(linked_element)
    element_category = get_element_category(linked_element)
    element_workset = get_element_workset(linked_element, linked_doc)
    linked_model_name = get_linked_doc_name(linked_doc)
    linked_id_int = linked_element_id.IntegerValue
    link_inst_id_int = link_instance_id.IntegerValue

    # --- Debug output ---
    print_debug(reference, link_instance, linked_doc, linked_element)

    # --- Copy to clipboard ---
    clipboard_ok = copy_to_clipboard(linked_id_int)

    # --- Display results ---
    print("")
    print("=" * 50)
    print("LINKED ELEMENT INFORMATION")
    print("=" * 26)
    print("")
    print("Linked Model:")
    print("  {}".format(linked_model_name))
    print("")
    print("Category:")
    print("  {}".format(element_category))
    print("")
    print("Workset:")
    print("  {}".format(element_workset))
    print("")
    print("Element:")
    print("  {}".format(element_name))
    print("")
    print("Linked Element ID:")
    print("  {}".format(linked_id_int))
    print("")
    print("Link Instance ID:")
    print("  {}".format(link_inst_id_int))
    print("")
    print("=" * 50)
    print("")

    if clipboard_ok:
        print("Linked Element ID copied to clipboard.")
    else:
        print("Could not copy to clipboard. "
              "ID displayed above.")

    print("")
    print("-" * 50)
    print("Created by Hazem Sakr")
    print("Connect with me: https://www.linkedin.com/in/hazem-sakr/")
    print("-" * 50)

# =============================================================================
# RUN
# =============================================================================

main()
