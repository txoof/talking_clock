/* [Propeties] */
// Body X
body_x = 10;
// Body Y
body_y = 12;
// Body Z
body_z = 8.4;
// Shaft Length (over bushing)
shaft_len = 20;
// Shaft Diameter
shaft_dia = 6;
// Bushing Length (use 0 for no bushing)
bushing_len = 5;
// Bushing Dia
bushing_dia = 9;
// Contacts Len
contacts_len = 4;
// Contacts Position
contacts_pos = "bottom"; //[bottom, back]

/* [Configuration] */
// Epsilon added/subtracted to prevent z-fighting
eps = 0.001;//[0.001:0.005:0.1]

module contacts(contact_width=1.5,
                contact_thickness=0.5,
                contact_height=4,
                contact_spacing=2.5) {

    for (i = [0:2]) {
        translate([i * contact_spacing - contact_spacing - contact_width/2, - contact_thickness/2, 0])
            cube([contact_width, contact_thickness, contact_height]);
    }
}

module potentiometer(body_dim=[body_x, body_y, body_z], 
                     shaft_dia=shaft_dia, 
                     shaft_len=shaft_len,
                     bushing_dia=bushing_dia,
                     bushing_len=bushing_len,
                     center=false,
                     eps=eps,
                     fn=64) {
    union() {
        %cube(body_dim, center=true);
        translate([0, 0, body_dim[2]/2]) {
            cylinder(h=shaft_len, d=shaft_dia + eps, $fn=fn);
        }
        translate([0, 0, body_dim[2]/2]) {
            cylinder(h=bushing_len, d=bushing_dia, $fn=fn);
        }
        translate([0, body_dim[1]/2 -0.5, -4 - body_dim[2]/2]) {
            contacts();
        }
    }
}

module potentiometer_cutter(bushing_dia=bushing_dia,
                            shaft_dia=shaft_dia, fn=64) {

    cutter_dia = bushing_dia > shaft_dia ? bushing_dia : shaft_dia;
    circle(d=cutter_dia, $fn=fn);
}

// potentiometer();
// potentiometer_cutter();

