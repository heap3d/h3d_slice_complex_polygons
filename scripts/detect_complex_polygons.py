#!/usr/bin/python
# ================================
# (C)2026 Dmytro Holub
# heap3d@gmail.com
# --------------------------------
# modo python
# detect and process complex polygons. complex polygons are polygons with edge shared same polygon with two sides

import modo
import modo.constants as c

from h3d_slice_complex_polygons.scripts.complex_polygons_tools import (
    get_complex_polygons,
    detect_edge_loops,
    create_aligned_loc,
    select_complex_components,
    EDGE,
    )


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

    for complex_polygon_data in complex_polygons_data:
        edge_loops = detect_edge_loops(complex_polygon_data)
        for edge_loop in edge_loops:
            create_aligned_loc(complex_polygon_data.mesh, EDGE, edge_loop)

    select_complex_components(complex_polygons_data)


if __name__ == '__main__':
    main()
