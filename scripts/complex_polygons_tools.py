#!/usr/bin/python
# ================================
# (C)2026 Dmytro Holub
# heap3d@gmail.com
# --------------------------------
# modo python
# EMAG
# utilites for complex polygons detection and processing
# ================================

from typing import Iterable
from dataclasses import dataclass

import lx
import modo
from modo import Scene, Item, Mesh, MeshPolygon, MeshEdge, MeshVertex, Vector3
import modo.constants as c

from h3d_utilites.scripts.h3d_utils import (
    MeshComponent,
    SELECTION_MODE,
    set_selection_mode,
    drop_selection,
    parent_items_to,
    select_components,
    select_polygons,
    select_vertices,
    )

from h3d_utilites.scripts.h3d_debug import (
    execution_time,
    # h3dd,
    )


ITEM_SEL = SELECTION_MODE.ITEM.value
POLYGON_SEL = SELECTION_MODE.POLYGON.value
EDGE_SEL = SELECTION_MODE.EDGE.value
VERTEX_SEL = SELECTION_MODE.VERTEX.value


VertexPair = tuple[MeshVertex, MeshVertex]


@dataclass
class BoundingBox:
    corner1: Vector3
    corner2: Vector3


@execution_time
def get_complex_polygons(mesh: Mesh) -> list[MeshPolygon]:
    complex_edges = get_complex_edges(mesh)

    complex_polygons: set[MeshPolygon] = set()
    for edge in complex_edges:
        polygons = edge.polygons
        if not polygons:
            continue
        complex_polygons.update(polygons)

    return list(complex_polygons)


def get_complex_edges(mesh: Mesh) -> list[MeshEdge]:
    geometry = mesh.geometry
    if not geometry:
        raise ValueError(f'Mesh <{mesh.name}> has no geometry')
    polygons = geometry.polygons
    if not polygons:
        raise ValueError(f'Mesh <{mesh.name}> has no polygons')

    one_polygon_edges = get_one_polygon_edges(polygons)
    open_edges = get_open_edges_all(polygons)
    complex_edges = set(one_polygon_edges) - set(open_edges)

    return list(complex_edges)


def get_one_polygon_edges(polygons: Iterable[MeshPolygon]) -> list[MeshEdge]:
    meshes = get_containing_meshes(polygons)
    if not meshes:
        raise ValueError('No meshes found for polygons')

    selected_edges: set[MeshEdge] = set()
    for mesh in meshes:
        mesh.select(replace=True)
        drop_selection(POLYGON_SEL)
        drop_selection(EDGE_SEL)

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


def get_containing_meshes(components: Iterable[MeshComponent]) -> list[Mesh]:
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
        drop_selection(POLYGON_SEL)
        drop_selection(EDGE_SEL)

        # Select boundary edges
        lx.eval('script.run "macro.scriptservice:92663570022:macro"')

        geometry = mesh.geometry
        if not geometry:
            raise ValueError(f'Mesh <{mesh.name}> has no geometry')
        edges = geometry.edges
        if not edges:
            raise ValueError(f'Mesh <{mesh.name}> has no edges')

        selected_edges.update(edges.selected)
        drop_selection(EDGE_SEL)

    return list(selected_edges)


def create_aligned_loc(component_type: str, components: Iterable[MeshComponent]) -> Item:
    LOCATOR_NAME = 'ComplexPolygon_Loc'

    if not is_component_mode(component_type):
        raise ValueError('Component type must be vertex, edge or polygon')

    drop_selection(POLYGON_SEL)
    drop_selection(EDGE_SEL)
    drop_selection(VERTEX_SEL)

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

    drop_selection(ITEM_SEL)
    for mesh in meshes:
        mesh.select()
    set_selection_mode(component_type)
    select_components(components_by_type)

    lx.eval('workPlane.fitSelect')
    drop_selection(VERTEX_SEL)
    drop_selection(EDGE_SEL)
    drop_selection(POLYGON_SEL)

    set_selection_mode(ITEM_SEL)
    locator = Scene().addItem(itype=c.LOCATOR_TYPE, name=LOCATOR_NAME)

    locator.select(replace=True)
    lx.eval('item.matchWorkplane pos')
    lx.eval('item.matchWorkplane rot')

    lx.eval('workPlane.reset')

    return locator


def is_component_of_type(component: MeshComponent, component_type: str) -> bool:
    if component_type == VERTEX_SEL:
        return isinstance(component, MeshVertex)
    elif component_type == EDGE_SEL:
        return isinstance(component, MeshEdge)
    elif component_type == POLYGON_SEL:
        return isinstance(component, MeshPolygon)
    else:
        raise ValueError('Component type must be vertex, edge or polygon')


def is_component_mode(select_type: str) -> bool:
    return select_type in (VERTEX_SEL, EDGE_SEL, POLYGON_SEL)


def get_bb_area(bbox: tuple[Vector3, Vector3]) -> float:
    x = Vector3(bbox[1]).x - Vector3(bbox[0]).x
    z = Vector3(bbox[1]).z - Vector3(bbox[0]).z

    return x * z


def get_containing_mesh(component: MeshComponent) -> Mesh:
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

    return mesh


@execution_time
def get_shadow_vertex_pairs(polygon: MeshPolygon) -> tuple[list[VertexPair], Item]:
    tmp_loc = create_aligned_loc(POLYGON_SEL, (polygon,))

    drop_selection(ITEM_SEL)
    drop_selection(POLYGON_SEL)
    drop_selection(EDGE_SEL)
    drop_selection(VERTEX_SEL)
    set_selection_mode(POLYGON_SEL)

    polygon.select()

    # select boundary edges
    lx.eval('@AddBoundary.py')
    lx.eval('copy')

    shadow_mesh = modo.Scene().addMesh('shadow_mesh')

    shadow_mesh.select(replace=True)
    parent_items_to((shadow_mesh,), tmp_loc, inplace=False)
    lx.eval('paste')

    lx.eval('layer.unmergeMeshes')

    bb_area: dict[Item, float] = dict()
    loc_children: list[Item] = tmp_loc.children()
    if not loc_children:
        raise ValueError('Error creating tmp mesh')

    for mesh in loc_children:
        geometry = mesh.geometry
        if not geometry:
            raise ValueError('Mesh item contains no geometry')

        bb_area[mesh] = get_bb_area((geometry.boundingBox))

    bb_area_sorted = sorted(list(bb_area.items()), key=lambda x: x[1], reverse=True)

    bb_area_sorted[0][0].select(replace=True)
    lx.eval('item.editorColor red')

    boundary_loop = bb_area_sorted[0][0]
    internal_loops = [bb_area[0] for bb_area in bb_area_sorted]

    shadow_vertex_pairs_distance: dict[VertexPair, float] = dict()
    for loop_mesh in internal_loops:
        for internal_vertex in loop_mesh.geometry.vertices:
            for boundary_vertex in boundary_loop.geometry.vertices:
                pos_boundary = Vector3(boundary_vertex.position)
                pos_internal = Vector3(internal_vertex.position)
                distance = Vector3(pos_boundary-pos_internal).length()

                shadow_vertex_pairs_distance[(boundary_vertex, internal_vertex)] = distance

    shadow_vertex_pairs_distance_sorted = sorted(list(shadow_vertex_pairs_distance.items()), key=lambda x: x[1])
    shadow_vertex_pairs = [vertex_pair[0] for vertex_pair in shadow_vertex_pairs_distance_sorted]

    return shadow_vertex_pairs, tmp_loc


def slice_by_vertex_pair(shadow_vertex_pair: VertexPair, polygon: MeshPolygon) -> bool:
    shadow_vector1 = Vector3(shadow_vertex_pair[0].position())
    shadow_vector2 = Vector3(shadow_vertex_pair[1].position())

    vertex1 = get_vertex_by_coords(polygon, shadow_vector1)
    vertex2 = get_vertex_by_coords(polygon, shadow_vector2)

    slice_polygon(polygon, (vertex1, vertex2))

    return False


def get_vertex_by_coords(polygon: MeshPolygon, position: Vector3) -> MeshVertex:
    # lx.eval("select.channel {mesh004:wposMatrix@lmb=x} set")
    ...


def slice_polygon(polygon: MeshPolygon, vertex_pair: VertexPair):
    mesh = get_containing_mesh(polygon)

    set_selection_mode(ITEM_SEL)
    mesh.select(replace=True)

    set_selection_mode(POLYGON_SEL)
    drop_selection(POLYGON_SEL)
    select_polygons((polygon,))

    set_selection_mode(VERTEX_SEL)
    drop_selection(VERTEX_SEL)
    select_vertices(vertex_pair)

    lx.eval('poly.split')


def is_polygon_complex(polygon: MeshPolygon) -> bool:
    ...
