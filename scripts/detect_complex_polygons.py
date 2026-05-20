#!/usr/bin/python
# ================================
# (C)2026 Dmytro Holub
# heap3d@gmail.com
# --------------------------------
# modo python
# detect and process complex polygons. complex polygons are polygons with edge shared same polygon with two sides

import modo
import modo.constants as c

from h3d_utilites.scripts.h3d_utils import drop_selection, set_selection_mode, select_if_exists, execution_time_alarm

from h3d_slice_complex_polygons.scripts.complex_polygons_tools import (
    get_complex_geometry,
    detect_edge_loops,
    create_aligned_loc,
    select_components,
    get_containing_meshes,
    get_open_edges_specified,
    POLYGON,
    EDGE,
    )

from h3d_utilites.scripts.h3d_debug import (
    h3dd,
    # execution_time,
    # prints,
    )


@execution_time_alarm
def main():
    meshes = modo.Scene().selectedByType(itype=c.MESH_TYPE)
    if not meshes:
        print('No meshes selected')
        return

    complex_polygons: list[modo.MeshPolygon] = []
    complex_edges: list[modo.MeshEdge] = []
    for mesh in meshes:
        polygons, edges = get_complex_geometry(mesh)
        complex_polygons.extend(polygons)
        complex_edges.extend(edges)

    if not complex_polygons:
        print('No complex polygons found')
        return

    boundary_edges = get_open_edges_specified(complex_polygons)

    edge_loops = detect_edge_loops(boundary_edges)
    for edge_loop in edge_loops:
        create_aligned_loc(EDGE, edge_loop)

    select_if_exists(get_containing_meshes(complex_polygons))

    set_selection_mode(POLYGON)
    drop_selection(POLYGON)
    select_components(complex_polygons)

    drop_selection(EDGE)
    for edge_loop in edge_loops:
        select_components(edge_loop)


if __name__ == '__main__':
    h3dd.enable_debug_output(True)
    main()
