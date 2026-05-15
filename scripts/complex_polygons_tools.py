#!/usr/bin/python
# ================================
# (C)2026 Dmytro Holub
# heap3d@gmail.com
# --------------------------------
# modo python
# EMAG
# utilites for complex polygons detection and processing
# ================================

from typing import Iterable, Optional, Union
from dataclasses import dataclass

import lx
import modo
import modo.constants as c

from h3d_utilites.scripts.h3d_utils import SELECTION_MODE, set_selection_mode, drop_selection


POLYGON = SELECTION_MODE.POLYGON.value
ITEM = SELECTION_MODE.ITEM.value
EDGE = SELECTION_MODE.EDGE.value
VERTEX = SELECTION_MODE.VERTEX.value


@dataclass
class ComplexPolygon:
    polygon: modo.MeshPolygon
    complex_edges: list[modo.MeshEdge]
    mesh: modo.Mesh


@dataclass
class VertexPair:
    vertex1: modo.MeshVertex
    vertex2: modo.MeshVertex


@dataclass
class BoundingBox:
    min: modo.Vector3
    max: modo.Vector3


Component = Union[modo.MeshVertex, modo.MeshEdge, modo.MeshPolygon]


def get_complex_polygons(mesh: modo.Mesh) -> list[ComplexPolygon]:
    if not mesh:
        raise ValueError('Mesh is None')

    complex_edges = get_complex_edges(mesh)

    complex_polygons = set()
    for edge in complex_edges:
        polygons = edge.polygons
        if not polygons:
            continue
        complex_polygons.update(polygons)

    complex_polygons_data = []
    for polygon in complex_polygons:
        complex_polygon = ComplexPolygon(
            polygon=polygon,
            complex_edges=[edge for edge in complex_edges if polygon in edge.polygons],
            mesh=mesh
        )
        complex_polygons_data.append(complex_polygon)

    return complex_polygons_data


def get_complex_edges(mesh: modo.Mesh) -> list[modo.MeshEdge]:
    if not mesh:
        raise ValueError('Mesh is None')

    one_polygon_edges = get_one_polygon_edges(mesh)
    open_edges = get_open_edges(mesh)
    complex_edges = set(one_polygon_edges) - set(open_edges)

    return list(complex_edges)


def get_one_polygon_edges(mesh: modo.Mesh) -> list[modo.MeshEdge]:

    if not mesh:
        raise ValueError('Mesh is None')

    mesh.select(replace=True)
    lx.eval('select.edge add poly equal 1')

    geometry = mesh.geometry
    if not geometry:
        raise ValueError('Mesh has no geometry')

    edges = geometry.edges
    if not edges:
        raise ValueError('Mesh has no edges')

    selected_edges = edges.selected
    lx.eval('select.drop edge')

    return selected_edges


def get_open_edges(mesh: modo.Mesh) -> list[modo.MeshEdge]:
    if not mesh:
        raise ValueError('Mesh is None')

    select_boundary_edges(mesh, None)

    geometry = mesh.geometry
    if not geometry:
        raise ValueError('Mesh has no geometry')

    edges = geometry.edges
    if not edges:
        raise ValueError('Mesh has no edges')

    selected_edges = edges.selected
    lx.eval('select.drop edge')

    return selected_edges


def select_boundary_edges(mesh: modo.Mesh, polygons: Optional[Iterable[modo.MeshPolygon]]):
    if not mesh:
        raise ValueError('Mesh is None')

    mesh.select(replace=True)
    drop_selection(POLYGON)
    if polygons:
        for polygon in polygons:
            polygon.select()

    # Select boundary edges
    lx.eval('script.run "macro.scriptservice:92663570022:macro"')


def select_complex_components(complex_polygons: Iterable[ComplexPolygon]):
    modo.Scene().deselect()
    set_selection_mode(POLYGON)
    drop_selection(POLYGON)

    for complex_polygon in complex_polygons:
        complex_polygon.polygon.select()
        complex_polygon.mesh.select()
        for edge in complex_polygon.complex_edges:
            edge.select()


def create_aligned_loc(mesh: modo.Mesh, component_type: str, components: Iterable[Component]) -> modo.Item:
    LOCATOR_NAME = 'ComplexPolygon_Loc'

    if not mesh:
        raise ValueError('Mesh is None')

    if not component_type:
        raise ValueError('Component type is None')

    if not components:
        raise ValueError('Components is None')

    if not is_component_mode(component_type):
        raise ValueError('Component type must be vertex, edge or polygon')

    mesh.select(replace=True)
    set_selection_mode(component_type)
    select_components(mesh, component_type, components)

    lx.eval('workPlane.fitSelect')
    drop_selection(VERTEX)
    drop_selection(EDGE)
    drop_selection(POLYGON)

    set_selection_mode(ITEM)
    locator = modo.Scene().addItem(itype=c.LOCATOR_TYPE, name=LOCATOR_NAME)

    locator.select(replace=True)
    lx.eval('item.matchWorkplane pos')
    lx.eval('item.matchWorkplane rot')

    lx.eval('workPlane.reset')

    return locator


def select_components(mesh: modo.Mesh, select_type: str, components: Iterable[Component], replace: bool = True):
    if not mesh or not isinstance(mesh, modo.Mesh):
        raise TypeError('Invalid mesh provided.')

    if not mesh.geometry:
        raise ValueError('Mesh has no geometry.')

    lx.eval(f'select.type {select_type}')
    if select_type not in (VERTEX, EDGE, POLYGON):
        return

    lx.eval(f'select.drop {select_type}')

    if select_type == VERTEX:
        if mesh.geometry.vertices:
            mesh.geometry.vertices.select(vertices=components)
    if select_type == EDGE:
        if mesh.geometry.edges:
            mesh.geometry.edges.select(edges=components)
    if select_type == POLYGON:
        if mesh.geometry.polygons:
            mesh.geometry.polygons.select(polygons=components)


def is_component_mode(select_type: str) -> bool:
    return select_type in (VERTEX, EDGE, POLYGON)


def detect_edge_loops(complex_poly: ComplexPolygon) -> list[list[modo.MeshEdge]]:
    ...


def get_edges_bounding_box(edges: Iterable[modo.MeshEdge], complex_poly: ComplexPolygon) -> BoundingBox:
    ...


def is_intersect(vertex_pair: VertexPair, edges: Iterable[modo.MeshEdge], complex_poly: ComplexPolygon) -> bool:
    ...


def is_polygon_complex(polygon: modo.MeshPolygon) -> bool:
    ...
