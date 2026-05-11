#!/usr/bin/python
# ================================
# (C)2026 Dmytro Holub
# heap3d@gmail.com
# --------------------------------
# modo python
# detect complex polygons

from typing import Iterable, Optional

import lx
import modo
import modo.constants as c

from h3d_utilites.scripts.h3d_utils import select_if_exists


def main():
    meshes = get_seleted_meshes()
    if not meshes:
        print('No meshes selected')
        return

    complex_polygons = []
    for mesh in meshes:
        complex_polygons.extend(get_complex_polygons(mesh))

    if not complex_polygons:
        print('No complex polygons found')
        return

    select_meshes_by_polygons(complex_polygons, meshes)


def get_seleted_meshes() -> list[modo.Mesh]:
    return modo.Scene().selectedByType(itype=c.MESH_TYPE)


def get_complex_polygons(mesh: modo.Mesh) -> list[modo.MeshPolygon]:
    if not mesh:
        raise ValueError('Mesh is None')

    one_polygon_edges = get_one_polygon_edges(mesh)
    open_edges = get_open_edges(mesh)
    complex_edges = set(one_polygon_edges) - set(open_edges)

    complex_polygons = []
    for edge in complex_edges:
        complex_polygons.extend(edge.polygons)

    return complex_polygons


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

    mesh.select(replace=True)
    lx.eval('select.drop polygon')
    lx.eval('script.run "macro.scriptservice:92663570022:macro"')

    geometry = mesh.geometry
    if not geometry:
        raise ValueError('Mesh has no geometry')

    edges = geometry.edges
    if not edges:
        raise ValueError('Mesh has no edges')

    selected_edges = edges.selected
    lx.eval('select.drop edge')

    return selected_edges


def get_item_by_selected_polygons(meshes: Iterable[modo.Mesh]) -> list[modo.Mesh]:
    selected_by_polys = [i for i in meshes if i.geometry.polygons.selected]  # type: ignore

    return selected_by_polys


def select_meshes_by_polygons(polygons: Iterable[modo.MeshPolygon], meshes: Optional[Iterable[modo.Mesh]] = None):
    if not polygons:
        print('No polygons to select')
        return

    if not meshes:
        meshes = modo.Scene().selectedByType(itype=c.MESH_TYPE)

    lx.eval('item.componentMode polygon true')
    lx.eval('select.drop polygon')
    for polygon in polygons:
        polygon.select()

    modo.Scene().deselect()
    complex_meshes = get_item_by_selected_polygons(meshes)
    select_if_exists(complex_meshes)


if __name__ == '__main__':
    main()
