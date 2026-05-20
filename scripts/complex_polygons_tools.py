#!/usr/bin/python
# ================================
# (C)2026 Dmytro Holub
# heap3d@gmail.com
# --------------------------------
# modo python
# EMAG
# utilites for complex polygons detection and processing
# ================================

from typing import Iterable, Union
from dataclasses import dataclass

import lx
from modo import Scene, Item, Mesh, MeshPolygon, MeshEdge, MeshVertex, Vector3
import modo.constants as c

from h3d_utilites.scripts.h3d_utils import SELECTION_MODE, set_selection_mode, drop_selection

from h3d_utilites.scripts.h3d_debug import (
    execution_time,
    # fn_in,
    # fn_out,
    # prints,
    )


ITEM = SELECTION_MODE.ITEM.value
POLYGON = SELECTION_MODE.POLYGON.value
EDGE = SELECTION_MODE.EDGE.value
VERTEX = SELECTION_MODE.VERTEX.value


@dataclass
class BoundingBox:
    corner1: Vector3
    corner2: Vector3


Component = Union[MeshVertex, MeshEdge, MeshPolygon]


@execution_time
def get_complex_geometry(mesh: Mesh) -> tuple[list[MeshPolygon], list[MeshEdge]]:
    # fn_in()
    complex_edges = get_complex_edges(mesh)

    complex_polygons: set[MeshPolygon] = set()
    for edge in complex_edges:
        polygons = edge.polygons
        if not polygons:
            continue
        complex_polygons.update(polygons)

    # fn_out()
    return list(complex_polygons), list(complex_edges)


# @execution_time
def get_complex_edges(mesh: Mesh) -> list[MeshEdge]:
    # fn_in()
    geometry = mesh.geometry
    if not geometry:
        raise ValueError(f'Mesh <{mesh.name}> has no geometry')
    polygons = geometry.polygons
    if not polygons:
        raise ValueError(f'Mesh <{mesh.name}> has no polygons')

    one_polygon_edges = get_one_polygon_edges(polygons)
    open_edges = get_open_edges_all(polygons)
    complex_edges = set(one_polygon_edges) - set(open_edges)

    # fn_out()
    return list(complex_edges)


@execution_time
def get_one_polygon_edges(polygons: Iterable[MeshPolygon]) -> list[MeshEdge]:
    meshes = get_containing_meshes(polygons)
    if not meshes:
        raise ValueError('No meshes found for polygons')

    selected_edges: set[MeshEdge] = set()
    for mesh in meshes:
        mesh.select(replace=True)
        drop_selection(POLYGON)
        drop_selection(EDGE)

        # select all 1-polygon edges
        lx.eval('select.edge add poly equal 1')

        geometry = mesh.geometry
        if not geometry:
            raise ValueError(f'Mesh <{mesh.name}> has no geometry')
        edges = geometry.edges
        if not edges:
            raise ValueError(f'Mesh <{mesh.name}> has no edges')

        selected_edges.update(edges.selected)
        lx.eval('select.drop edge')

    return [edge for edge in selected_edges if is_edge_belong_to(edge, polygons)]


@execution_time
def get_containing_meshes(components: Iterable[Component]) -> list[Mesh]:
    meshes: set[Mesh] = set()
    for component in components:
        geometry = component._geometry
        if not geometry:
            raise ValueError('Component has no geometry')
        item = geometry._item
        if not item:
            raise ValueError('Geometry has no item')
        id = item.Ident()
        if id is None:
            raise ValueError('Item has no id')
        mesh = Mesh(id)
        if not mesh:
            raise ValueError(f'Mesh with id {id} not found')
        meshes.add(mesh)

    return list(meshes)


def is_edge_belong_to(edge: MeshEdge, polygons: Iterable[MeshPolygon]) -> bool:
    for polygon in edge.polygons:
        if polygon in polygons:
            return True

    return False


@execution_time
def get_open_edges_all(polygons: Iterable[MeshPolygon]) -> list[MeshEdge]:
    meshes = get_containing_meshes(polygons)
    if not meshes:
        raise ValueError('No meshes found for polygons')

    selected_edges: set[MeshEdge] = set()
    for mesh in meshes:
        mesh.select(replace=True)
        drop_selection(POLYGON)
        drop_selection(EDGE)

        # Select boundary edges
        lx.eval('script.run "macro.scriptservice:92663570022:macro"')

        geometry = mesh.geometry
        if not geometry:
            raise ValueError(f'Mesh <{mesh.name}> has no geometry')
        edges = geometry.edges
        if not edges:
            raise ValueError(f'Mesh <{mesh.name}> has no edges')

        selected_edges.update(edges.selected)
        drop_selection(EDGE)

    return list(selected_edges)


@execution_time
def get_open_edges_specified(polygons: Iterable[MeshPolygon]) -> list[MeshEdge]:
    meshes = get_containing_meshes(polygons)
    if not meshes:
        raise ValueError('No meshes found for polygons')

    selected_edges: set[MeshEdge] = set()
    for mesh in meshes:
        mesh.select(replace=True)
        drop_selection(POLYGON)
        drop_selection(EDGE)

        for polygon in polygons:
            polygon.select()

        # Select boundary edges
        lx.eval('script.run "macro.scriptservice:92663570022:macro"')

        geometry = mesh.geometry
        if not geometry:
            raise ValueError(f'Mesh <{mesh.name}> has no geometry')
        edges = geometry.edges
        if not edges:
            raise ValueError(f'Mesh <{mesh.name}> has no edges')

        selected_edges.update(edges.selected)
        drop_selection(EDGE)

    return list(selected_edges)


@execution_time
def select_components(components: Iterable[Component]):
    for component in components:
        component.select()


@execution_time
def create_aligned_loc(component_type: str, components: Iterable[Component]) -> Item:
    LOCATOR_NAME = 'ComplexPolygon_Loc'

    if not is_component_mode(component_type):
        raise ValueError('Component type must be vertex, edge or polygon')

    drop_selection(POLYGON)
    drop_selection(EDGE)
    drop_selection(VERTEX)

    components_by_type = [
        component
        for component in components
        if is_component_of_type(component, component_type)
        ]
    if not components_by_type:
        raise ValueError(f'No components of type {component_type} found in the list')

    meshes = get_containing_meshes(components_by_type)
    if not meshes:
        raise ValueError('No meshes found for components')

    drop_selection(ITEM)
    for mesh in meshes:
        mesh.select()
    set_selection_mode(component_type)
    select_components(components_by_type)

    lx.eval('workPlane.fitSelect')
    drop_selection(VERTEX)
    drop_selection(EDGE)
    drop_selection(POLYGON)

    set_selection_mode(ITEM)
    locator = Scene().addItem(itype=c.LOCATOR_TYPE, name=LOCATOR_NAME)

    locator.select(replace=True)
    lx.eval('item.matchWorkplane pos')
    lx.eval('item.matchWorkplane rot')

    lx.eval('workPlane.reset')

    return locator


# @execution_time
def is_component_of_type(component: Component, component_type: str) -> bool:
    if component_type == VERTEX:
        return isinstance(component, MeshVertex)
    elif component_type == EDGE:
        return isinstance(component, MeshEdge)
    elif component_type == POLYGON:
        return isinstance(component, MeshPolygon)
    else:
        raise ValueError('Component type must be vertex, edge or polygon')


# @execution_time
def is_component_mode(select_type: str) -> bool:
    return select_type in (VERTEX, EDGE, POLYGON)


@execution_time
def detect_edge_loops(edges: Iterable[MeshEdge]) -> list[list[MeshEdge]]:
    """
    detect edge loops from the list of edges. Edge loop is a sequence of connected edges.
    """
    # fn_in()
    edges_to_process = set(edges)
    edge_loops: list[list[MeshEdge]] = []
    while edges_to_process:
        edge = edges_to_process.pop()
        connected_edges = get_connected_edges(edge, edges_to_process)
        edge_loops.append([edge] + connected_edges)
        edges_to_process -= set(connected_edges)

    # fn_out()
    return edge_loops


# @execution_time
def get_connected_edges(edge: MeshEdge, edges_to_test: Iterable[MeshEdge]) -> list[MeshEdge]:
    testing_edges = set(edges_to_test) - {edge}
    for test_edge in testing_edges:
        if is_connected(test_edge, edge):
            return [test_edge, ] + get_connected_edges(test_edge, testing_edges - {test_edge})

    return []


def is_connected(edge1: MeshEdge, edge2: MeshEdge) -> bool:
    return any(vertex in edge2.vertices for vertex in edge1.vertices)


def get_edges_bounding_box(edges: Iterable[MeshEdge], polygon: MeshPolygon) -> BoundingBox:
    ...


def is_polygon_complex(polygon: MeshPolygon) -> bool:
    ...
