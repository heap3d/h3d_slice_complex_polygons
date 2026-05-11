#!/usr/bin/python
# ================================
# (C)2026 Dmytro Holub
# heap3d@gmail.com
# --------------------------------
# modo python
# detect complex polygons

from typing import Iterable, Optional
from dataclasses import dataclass

import lx
import modo
import modo.constants as c


@dataclass
class ComplexPolygon:
    polygon: modo.MeshPolygon
    complex_edges: list[modo.MeshEdge]
    mesh: modo.Mesh


def main():
    meshes = modo.Scene().selectedByType(itype=c.MESH_TYPE)
    if not meshes:
        print('No meshes selected')
        return

    complex_polygons_data = []
    for mesh in meshes:
        complex_polygons_data.extend(get_complex_polygons(mesh))

    if not complex_polygons_data:
        print('No complex polygons found')
        return

    select_complex_components(complex_polygons_data)


def select_complex_components(complex_polygons: Iterable[ComplexPolygon]):
    modo.Scene().deselect()
    lx.eval('item.componentMode polygon true')
    lx.eval('select.drop polygon')

    for complex_polygon in complex_polygons:
        complex_polygon.polygon.select()
        complex_polygon.mesh.select()
        for edge in complex_polygon.complex_edges:
            edge.select()


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


def get_item_by_selected_polygons(meshes: Iterable[modo.Mesh]) -> list[modo.Mesh]:
    selected_by_polys = [i for i in meshes if i.geometry.polygons.selected]  # type: ignore

    return selected_by_polys


# def select_meshes_by_polygons(polygons: Iterable[modo.MeshPolygon], meshes: Optional[Iterable[modo.Mesh]] = None):
#     if not polygons:
#         print('No polygons to select')
#         return

#     if not meshes:
#         meshes = modo.Scene().selectedByType(itype=c.MESH_TYPE)

#     lx.eval('item.componentMode polygon true')
#     lx.eval('select.drop polygon')
#     for polygon in polygons:
#         polygon.select()

#     modo.Scene().deselect()
#     complex_meshes = get_item_by_selected_polygons(meshes)
#     select_if_exists(complex_meshes)


def select_boundary_edges(mesh: modo.Mesh, polygons: Optional[Iterable[modo.MeshPolygon]]):
    if not mesh:
        raise ValueError('Mesh is None')

    mesh.select(replace=True)
    lx.eval('select.drop polygon')
    if polygons:
        for polygon in polygons:
            polygon.select()

    lx.eval('script.run "macro.scriptservice:92663570022:macro"')


if __name__ == '__main__':
    main()
