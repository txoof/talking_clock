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

%cube([grill_x, grill_y, 1], center=true);

pitch_x = 2 * r + gap;
pitch_y = sqrt(3) * (r + gap / 2);

count_x = ceil(grill_x / pitch_x) + 1;
count_y = ceil(grill_y / pitch_y);

x0 = -((count_x - 1) * pitch_x) / 2;
y0 = -((count_y - 1) * pitch_y) / 2;

for (iy = [0 : count_y - 1]) {
    row_offset = (iy % 2) * pitch_x / 2;
    row_rot = (iy % 2 == 0) ? even_rot : odd_rot;

    for (ix = [0 : count_x - 1]) {
        translate([
            x0 + ix * pitch_x + row_offset,
            y0 + iy * pitch_y,
            0
        ]) {
            rotate([0, 0, row_rot]) {
                cylinder(r = r, h = h, center = true);
            }
        }
    }
}