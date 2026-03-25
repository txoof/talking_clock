/* [Hole Style] */
// Roundness
$fn = 6;
// Radius
r = 2;
// Gap
gap = 1.5;
// Even Rotation
even_rot = -30;
// Odd Rotation
odd_rot = 30;

grill_x = 30;
grill_y = 30;

h = 10;

eps = .001;

module hole_shape(mode_2d=true, r=2, h=10, rot=0, hole_sides=6) {
    if (mode_2d) {
        rotate(rot)
            circle(r=r, $fn=hole_sides);
    } else {
        rotate([0, 0, rot])
            cylinder(r=r, h=h, center=true, $fn=hole_sides);
    }
}

module cutter_pos(
    grill_x=grill_x,
    grill_y=grill_y,
    h=h,
    r=r,
    hole_sides=6,
    gap=gap,
    even_rot=even_rot,
    odd_rot=odd_rot,
    mode_2d=false
) {
    pitch_x = 2 * r + gap;
    pitch_y = sqrt(3) * (r + gap / 2);

    count_x = ceil(grill_x / pitch_x) + 1;
    count_y = ceil(grill_y / pitch_y);

    x0 = -((count_x - 1) * pitch_x) / 2;
    y0 = -((count_y - 1) * pitch_y) / 2;

    odd_rows = floor(count_y / 2);
    x_com_shift = (odd_rows / count_y) * (pitch_x / 2);

    for (iy = [0 : count_y - 1]) {
        row_offset = (iy % 2) * pitch_x / 2;
        row_rot = (iy % 2 == 0) ? even_rot : odd_rot;

        for (ix = [0 : count_x - 1]) {
            if (mode_2d) {
                translate([
                    x0 + ix * pitch_x + row_offset - x_com_shift,
                    y0 + iy * pitch_y
                ]) {
                    hole_shape(
                        mode_2d=true,
                        r=r,
                        h=h,
                        rot=row_rot,
                        hole_sides=hole_sides
                    );
                }
            } else {
                translate([
                    x0 + ix * pitch_x + row_offset - x_com_shift,
                    y0 + iy * pitch_y,
                    0
                ]) {
                    hole_shape(
                        mode_2d=false,
                        r=r,
                        h=h,
                        rot=row_rot,
                        $fn=$fn
                    );
                }
            }
        }
    }
}


module cutter_circle(
    d=30,
    h=10,
    hole_r=2,
    gap=2,
    even_rot=30,
    odd_rot=30,
    hole_sides=6,
    mode_2d=true,
    $fn=64
) {
    inner_d = d;
    outer_d = 2 * d;
    
    difference() {
        cutter_pos(
            grill_x=d,
            grill_y=d,
            r=hole_r,
            h=h,
            gap=gap,
            even_rot=even_rot,
            odd_rot=odd_rot,
            hole_sides=hole_sides,
            mode_2d=mode_2d
        );

        if (mode_2d) {
            difference() {
                circle(d=outer_d, $fn=$fn);
                circle(d=inner_d, $fn=$fn);
            }
        } else {
            difference() {
                cylinder(h=h + eps, d=outer_d, center=true, $fn=$fn);
                cylinder(h=h, d=inner_d, center=true, $fn=$fn);
            }
        }
    }
}

module cutter_square(
    x=30,
    y=30,
    h=10,
    hole_r=2,
    gap=2,
    even_rot=30,
    odd_rot=30,
    hole_sides=6,
    mode_2d=true,
    $fn=64
) {
    inner_cube = [x, y, h];
    outer_cube = [2 * x, 2 * y, h];
    
    difference() {
        cutter_pos(
            grill_x=x,
            grill_y=y,
            r=hole_r,
            h=h,
            gap=gap,
            even_rot=even_rot,
            odd_rot=odd_rot,
            hole_sides=hole_sides,
            mode_2d=mode_2d
        );

        if (mode_2d) {
            difference() {
                square([2 * x, 2 * y], center=true);
                square([x, y], center=true);
            }
        } else {
            difference() {
                cube(outer_cube, center=true);
                cube(inner_cube, center=true);
            }
        }
    }
}

// 3D example
// difference() {
//     cube([32, 52, 1], center=true);
//     cutter_square(
//         x=30,
//         y=50,
//         h=2,
//         hole_r=2,
//         gap=.2,
//         hole_sides=4,
//         odd_rot=-15,
//         even_rot=15,
//         mode_2d=false
//     );
// }

// 2D example for use inside linear_extrude()
// difference() {
//     square([32, 52], center=true);
//     cutter_square(
//         x=30,
//         y=50,
//         hole_r=2,
//         gap=.2,
//         hole_sides=4,
//         odd_rot=-15,
//         even_rot=15,
//         mode_2d=true
//     );
// }