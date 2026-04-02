module chamfer_square(dim, r, center=false, fn=64) {
    $fn = fn;
    my_dim = [dim[0] - r * 2, dim[1] - r * 2];
    trans_coord = center ? [-my_dim[0] / 2, -my_dim[1] / 2, 0] : [r, r, 0];

    translate(trans_coord)
    minkowski() {
        circle(r);
        square(my_dim);
    }
}

/*
Return the standard ISO metric hex nut width across flats in mm
for a given nominal M size.

Supported sizes:
M2, M2.5, M3, M4, M5, M6, M8, M10, M12

Returns:
Across flats dimension in mm, or undef if the size is not supported.
*/
function nut_af(m) =
    m == 2   ? 4   :
    m == 2.5 ? 5   :
    m == 3   ? 5.5 :
    m == 4   ? 7   :
    m == 5   ? 8   :
    m == 6   ? 10  :
    m == 8   ? 13  :
    m == 10  ? 16  :
    m == 12  ? 18  :
    undef;

/*
Convert a nut width across flats into the radius needed for:
circle(r=..., $fn=6)

For a regular hexagon generated this way:
across_flats = sqrt(3) * r

Arguments:
af
    Width across flats in mm

Returns:
Hexagon radius in mm
*/
function hex_radius_from_af(af) = af / sqrt(3);

/*
Return the radius for a hexagonal nut trap sized for a given
ISO metric nut.

This value is intended for use as:
circle(r=nut_radius(...), $fn=6);

Arguments:
m
    Nominal metric size, such as 3 for M3 or 6 for M6
clearance
    Extra clearance added to the across flats dimension in mm

Returns:
Radius in mm for a 6 sided circle, or undef if the nut size
is not supported.
*/
function nut_radius(m, clearance=0) =
    hex_radius_from_af(nut_af(m) + clearance);

/*
Shared width for all sandwich plates.
Based on the nut trap radius, with extra room around the hex.
*/
function nut_plate_width(fastener_d=3, clearance=0.15) =
    nut_radius(m=fastener_d, clearance=clearance) * 3;

/*
Shared usable span along X.
This keeps holes and fingers away from the ends.
*/
function plate_x_min(length=50, fastener_d=3, clearance=0.15) =
    -length / 2 + 1.8 * nut_radius(m=fastener_d, clearance=clearance);

function plate_x_max(length=50, fastener_d=3, clearance=0.15) =
     length / 2 - 1.8 * nut_radius(m=fastener_d, clearance=clearance);

/*
Shared Z extent for the 3D sandwich.
*/
function sandwich_height(plate_thickness=3, middle_thickness=3, gap_z=0) =
    plate_thickness + gap_z + middle_thickness + gap_z + plate_thickness;

/*
Place children() N times across the shared usable span.
If n_items is 1, place it at x = 0.
*/
module plate_positions(length=50, n_items=3, fastener_d=3, clearance=0.15) {
    x_min = plate_x_min(length=length, fastener_d=fastener_d, clearance=clearance);
    x_max = plate_x_max(length=length, fastener_d=fastener_d, clearance=clearance);
    x_pitch = n_items > 1 ? (x_max - x_min) / (n_items - 1) : 0;

    for (i = [0 : n_items - 1]) {
        translate([n_items > 1 ? x_min + i * x_pitch : 0, 0]) {
            children();
        }
    }
}

/*
Place children() at each fastener center.
*/
module fastener_positions(length=50, n_fasteners=3, fastener_d=3, clearance=0.15) {
    plate_positions(
        length=length,
        n_items=n_fasteners,
        fastener_d=fastener_d,
        clearance=clearance
    ) {
        children();
    }
}

/*
Place children() at each finger center.
*/
module finger_positions(length=50, n_fingers=3, fastener_d=3, clearance=0.15) {
    plate_positions(
        length=length,
        n_items=n_fingers,
        fastener_d=fastener_d,
        clearance=clearance
    ) {
        children();
    }
}

/*
Shared outer profile for all plates.
*/
module nut_plate_blank(length=50, width=10, chamfer_r=.5) {
    chamfer_square(dim=[length, width], r=chamfer_r, center=true);
}

/*
One finger centered at the local origin.
*/
module finger_shape(finger_width=5, material=4, slot_clearance=0) {
    square([finger_width + slot_clearance, material + slot_clearance], center=true);
}

/*
Hex nut cutouts positioned on the plate.
*/
module nut_holes(length=50, n_fasteners=3, fastener_d=3, nut_clearance=0.15) {
    nut_r = nut_radius(m=fastener_d, clearance=nut_clearance);

    fastener_positions(
        length=length,
        n_fasteners=n_fasteners,
        fastener_d=fastener_d,
        clearance=nut_clearance
    ) {
        circle(r=nut_r, $fn=6);
    }
}

/*
Round bolt holes positioned on the plate.

hole_clearance
    Extra diameter added when using these as a cutter.
*/
module bolt_holes(length=50, n_fasteners=3, fastener_d=3,
                  hole_d=3.2, nut_clearance=0.15, hole_clearance=0) {
    fastener_positions(
        length=length,
        n_fasteners=n_fasteners,
        fastener_d=fastener_d,
        clearance=nut_clearance
    ) {
        circle(d=hole_d + hole_clearance, $fn=32);
    }
}

/*
Finger tabs attached to the +Y edge of a plate body.
*/
module finger_tabs(length=50, width=10, finger_width=5, material=4,
                   n_fingers=3, fastener_d=3, nut_clearance=0.15) {
    finger_positions(
        length=length,
        n_fingers=n_fingers,
        fastener_d=fastener_d,
        clearance=nut_clearance
    ) {
        translate([0, width / 2 + material / 2]) {
            finger_shape(finger_width=finger_width, material=material);
        }
    }
}

/*
Standalone finger slot cutters centered on the X axis.
Their long dimension is bisected by the X/Z plane.
*/
module finger_slots(length=50, finger_width=5, material=4,
                    n_fingers=3, fastener_d=3,
                    nut_clearance=0.15, slot_clearance=0.15) {
    finger_positions(
        length=length,
        n_fingers=n_fingers,
        fastener_d=fastener_d,
        clearance=nut_clearance
    ) {
        finger_shape(
            finger_width=finger_width,
            material=material,
            slot_clearance=slot_clearance
        );
    }
}

/*
Standalone bolt hole cutters centered on the X axis.
Their centers lie on the X/Z plane.
*/
module bolt_hole_cutter(length=50, n_fasteners=3, fastener_d=3,
                        hole_d=3.2, nut_clearance=0.15,
                        hole_clearance=0.15) {
    bolt_holes(
        length=length,
        n_fasteners=n_fasteners,
        fastener_d=fastener_d,
        hole_d=hole_d,
        nut_clearance=nut_clearance,
        hole_clearance=hole_clearance
    );
}

/*
Middle plate.
Hex nut traps plus fingers.
*/
module nut_finger_plate(length=50, finger_width=5, material=4,
                        n_fasteners=3, n_fingers=3, fastener_d=3,
                        nut_clearance=0.15, chamfer_r=.5) {
    width = nut_plate_width(fastener_d=fastener_d, clearance=nut_clearance);

    union() {
        difference() {
            nut_plate_blank(length=length, width=width, chamfer_r=chamfer_r);
            nut_holes(
                length=length,
                n_fasteners=n_fasteners,
                fastener_d=fastener_d,
                nut_clearance=nut_clearance
            );
        }

        finger_tabs(
            length=length,
            width=width,
            finger_width=finger_width,
            material=material,
            n_fingers=n_fingers,
            fastener_d=fastener_d,
            nut_clearance=nut_clearance
        );
    }
}

/*
Top and bottom plates.
Round clearance holes aligned with the nut traps.
*/
module nut_base_plate(length=50, n_fasteners=3, fastener_d=3,
                      hole_d=3.2, nut_clearance=0.15, chamfer_r=.5) {
    width = nut_plate_width(fastener_d=fastener_d, clearance=nut_clearance);

    difference() {
        nut_plate_blank(length=length, width=width, chamfer_r=chamfer_r);
        bolt_holes(
            length=length,
            n_fasteners=n_fasteners,
            fastener_d=fastener_d,
            hole_d=hole_d,
            nut_clearance=nut_clearance,
            hole_clearance=0
        );
    }
}

/*
2D cutter for slots that match the fingers.

Use this inside difference() on another panel.

slot_clearance
    Positive values make the slot slightly larger than the finger.
*/
module finger_slot_cutter(length=50, material=4, finger_width=5,
                          n_fingers=3, fastener_d=3,
                          nut_clearance=0.15, slot_clearance=0.15) {
    finger_slots(
        length=length,
        finger_width=finger_width,
        material=material,
        n_fingers=n_fingers,
        fastener_d=fastener_d,
        nut_clearance=nut_clearance,
        slot_clearance=slot_clearance
    );
}

/*
2D cutter for bolt holes that match the base plates.

Use this inside difference() on another panel.

hole_clearance
    Positive values make the bolt holes slightly larger.
*/
module bolt_hole_slot_cutter(length=50, n_fasteners=3, fastener_d=3,
                             hole_d=3.2, nut_clearance=0.15,
                             hole_clearance=0.15) {
    bolt_hole_cutter(
        length=length,
        n_fasteners=n_fasteners,
        fastener_d=fastener_d,
        hole_d=hole_d,
        nut_clearance=nut_clearance,
        hole_clearance=hole_clearance
    );
}

/*
2D layout for cutting:
two base plates and one finger plate
*/
module nut_sandwich_layout(length=50, finger_width=5, material=4,
                           n_fasteners=3, n_fingers=3, fastener_d=3,
                           hole_d=3.2, nut_clearance=0.15,
                           chamfer_r=.5) {
    width = nut_plate_width(fastener_d=fastener_d, clearance=nut_clearance);
    gap = material;
    base_pitch = width + gap;

    translate([0, base_pitch, 0]) {
        nut_finger_plate(
            length=length,
            finger_width=finger_width,
            material=material,
            n_fasteners=n_fasteners,
            n_fingers=n_fingers,
            fastener_d=fastener_d,
            nut_clearance=nut_clearance,
            chamfer_r=chamfer_r
        );
    }

    translate([0, 0, 0]) {
        nut_base_plate(
            length=length,
            n_fasteners=n_fasteners,
            fastener_d=fastener_d,
            hole_d=hole_d,
            nut_clearance=nut_clearance,
            chamfer_r=chamfer_r
        );
    }

    translate([0, -base_pitch, 0]) {
        nut_base_plate(
            length=length,
            n_fasteners=n_fasteners,
            fastener_d=fastener_d,
            hole_d=hole_d,
            nut_clearance=nut_clearance,
            chamfer_r=chamfer_r
        );
    }
}

/*
3D assembled sandwich:
base plate
middle finger plate
top base plate
*/
module nut_sandwich_3d(length=50, finger_width=5, material=4,
                       n_fasteners=3, n_fingers=3, fastener_d=3,
                       hole_d=3.2, nut_clearance=0.15,
                       chamfer_r=.5, plate_thickness=3,
                       middle_thickness=3, gap_z=0,
                       show_bolts=false) {

    total_height = sandwich_height(
        plate_thickness=plate_thickness,
        middle_thickness=middle_thickness,
        gap_z=gap_z
    );
    bolt_len = total_height + plate_thickness * 5;
    width = nut_plate_width(fastener_d=fastener_d, clearance=nut_clearance);

    z_middle = plate_thickness + gap_z;
    z_top = plate_thickness + gap_z + middle_thickness + gap_z;

    translate([0, -width / 2, -total_height / 2]) {
        color("dimgray")
        linear_extrude(height=plate_thickness) {
            nut_base_plate(
                length=length,
                n_fasteners=n_fasteners,
                fastener_d=fastener_d,
                hole_d=hole_d,
                nut_clearance=nut_clearance,
                chamfer_r=chamfer_r
            );
        }

        translate([0, 0, z_middle]) {
            color("linen")
            linear_extrude(height=middle_thickness) {
                nut_finger_plate(
                    length=length,
                    finger_width=finger_width,
                    material=material,
                    n_fasteners=n_fasteners,
                    n_fingers=n_fingers,
                    fastener_d=fastener_d,
                    nut_clearance=nut_clearance,
                    chamfer_r=chamfer_r
                );
            }
        }

        translate([0, 0, z_top]) {
            color("dimgray")
            linear_extrude(height=plate_thickness) {
                nut_base_plate(
                    length=length,
                    n_fasteners=n_fasteners,
                    fastener_d=fastener_d,
                    hole_d=hole_d,
                    nut_clearance=nut_clearance,
                    chamfer_r=chamfer_r
                );
            }
        }

        if (show_bolts) {
            color("silver")
            fastener_positions(
                length=length,
                n_fasteners=n_fasteners,
                fastener_d=fastener_d,
                clearance=nut_clearance
            ) {
                translate([0, 0, -plate_thickness * 2.5]) {
                    cylinder(d=hole_d * 0.9, h=bolt_len, $fn=32);
                }
            }
        }
    }
}

// !nut_sandwich_layout(
//     length=50,
//     finger_width=5,
//     material=4,
//     n_fasteners=2,
//     n_fingers=3,
//     fastener_d=3,
//     hole_d=3.2
// );

// !nut_sandwich_3d(
//     length=50,
//     finger_width=5,
//     material=4,
//     n_fasteners=2,
//     n_fingers=3,
//     fastener_d=3,
//     hole_d=3.2,
//     plate_thickness=3,
//     middle_thickness=3,
//     show_bolts=true
// );

// difference() {
//     square([80, 40], center=true);

//     finger_slot_cutter(
//         length=50,
//         material=4,
//         finger_width=5,
//         n_fingers=3,
//         fastener_d=3,
//         slot_clearance=0.15
//     );
// }

// difference() {
//     square([80, 40], center=true);

//     bolt_hole_slot_cutter(
//         length=50,
//         n_fasteners=2,
//         fastener_d=3,
//         hole_d=3.2,
//         hole_clearance=0.15
//     );
// }