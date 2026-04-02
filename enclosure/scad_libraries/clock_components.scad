module dupont_pins(count=4, pin_pitch=2.54, pin_thick=0.64, pin_len=6) {
    y0 = -((count - 1) * pin_pitch) / 2;

    for (i = [0 : count - 1]) {
        translate([0, y0 + i * pin_pitch, 0]) {
            cube([pin_len + 4, pin_thick, pin_thick], center=true);
        }
    }
}

module max_amp(dim, terminal_h) {
    pin_thick = 0.64;
    pin_len = 6;
    color("mediumslateblue") {
        cube(dim, center=true);
    }
    
    terminal_block_dim = [pin_thick*5, dim[1]/2, terminal_h];

    color("blue") {
        translate([-dim[0]/2 + terminal_block_dim[0]/2, 0, terminal_h/2+dim[2]/2]) {

            cube(terminal_block_dim, center=true);
        }

    }

    color("gold") {
        translate([dim[0]/2 - 1, 0, pin_len/2 + dim[2]/2]) {
            rotate([0, 90, 0])
            dupont_pins(
                count=7,
                pin_thick=pin_thick,
                pin_len=pin_len
            );
        }
    }
    color("white") {
        translate([0, 0, dim[2] / 2]) {
            linear_extrude(height=0.4) {
                text("MAX", size=3, halign="center", valign="center");
            }
        }
    }    
}

module rtc(dim) {
    pin_thick = .64;
    pin_len = 6; 

    color("blue") {
        cube(dim, center=true);
    }
    
    color("gold") {
        translate([dim[0] / 2 + pin_len / 2, 0, dim[2] / 2 + pin_thick / 2]) {
            dupont_pins(
                count=4,
                pin_thick=pin_thick,
                pin_len=pin_len
            );
        }
    }

    color("white") {
        translate([0, 0, dim[2] / 2]) {
            linear_extrude(height=0.4) {
                text("RTC", size=3, halign="center", valign="center");
            }
        }
    }
}

module sd_card_reader(dim) {
    pin_thick = .64;
    pin_len = 6;     
    color("green") {
        cube(dim, center=true);
    }

    color("gold") {
        translate([dim[0] / 2 + pin_len / 2, 0, 1 + pin_thick / 2]) {
            dupont_pins(
                count=6,
                pin_thick=pin_thick,
                pin_len=pin_len
            );
        }
    }
    color("white") {
        translate([0, 0, dim[2] / 2]) {
            linear_extrude(height=0.4) {
                text("SD Card", size=3, halign="center", valign="center");
            }
        }
    }

}

module pi_pico() {
    // Pico X Dimensions
    pico_x = 51.5;
    // Pico Y Dimensions
    pico_y = 21;    

    pin_thick = .64;
    pin_len = 6; 

    color("darkseagreen") {
        cube([pico_x, pico_y, 2], center=true);
    }

    color("gold") {
        translate([0, pico_y/2 - pin_thick*1.5, pin_len]) {
            rotate([90, 90, 0])
            dupont_pins(
                count=20,
                pin_thick=pin_thick,
                pin_len=pin_len
            );
        }
        translate([0, -pico_y/2 + pin_thick*1.5, pin_len]) {
            rotate([90, 90, 0])
            dupont_pins(
                count=20,
                pin_thick=pin_thick,
                pin_len=pin_len
            );
        }

    }    

    color("white") {
        translate([0, 0, 2 / 2]) {
            linear_extrude(height=0.4) {
                text("Pi Pico", size=3, halign="center", valign="center");
            }
        }
    } 

}

module box_speaker(dim=[50, 45, 22], ears=true, od=8, h=4) {
    color("gray") {
        union() {
            for (i = [-1, 1]) {
                translate([i*(dim[0]/2+od/2), 0, 0]) {
                    union() {
                        translate([i*-od/2, 0, 0]) {
                            cube([od, od, h], center=true);
                        }
                        cylinder(d=od, center=true, h=h);
                    }
                }
            }
            cube(dim, center=true);
        }
    }
}

module dupont_bus_bar(dim=[35, 5, 2], col=9) {
    pin_thick=.64;
    pin_len = 6;
    color("orange") {
        cube(dim, center=true);
    }
    for (i=[-1, 1]) {
        translate([0, i*(dim[1]/2 - pin_thick), pin_len/2]) {
            rotate([0, 90, 90])
            dupont_pins(count=col);
        }
    }

    color("white") {
        translate([0, 0, 2 / 2]) {
            linear_extrude(height=0.4) {
                text("Bus Bar", size=3, halign="center", valign="center");
            }
        }
    } 

}
