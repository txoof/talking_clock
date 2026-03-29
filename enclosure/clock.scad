use <./scad_libraries/finger_joint_box.scad>
use <./scad_libraries/clock_components.scad>
use<./scad_libraries/cone_speaker.scad>
use<./scad_libraries/speaker_grill.scad>
use<./scad_libraries/arcade_button.scad>
use<./scad_libraries/fasteners.scad>
use<./scad_libraries/cone_speaker.scad>


/* [Rendering Setup] */

three_d = 1;

/* [Enclosure Dimensions] */
// Average material thickness (mm)
material = 4.0;
// Finger Joint Width in (mm)
finger = 5;

// Exterior Width
case_x = 130;
// Exterior Depth
case_y = 102;
// Exterior Height
case_z = 58; 

/* [Font] */
font = "Impact";


/* [USB Port] */
// Port X width
usb_port_x = 12;
// port Z height
usb_port_z = 10.5;

/* [Speaker] */
// box speaker
speaker_dim = [50, 45, 22];
// mounting ears
ears=true;
// ear outer dia
ear_od=8;
// ear height
ear_h=4;

/* [Cone Speaker] */
cone_dia = 78;
cone_magnet_dia = 36;
cone_height = 27;

/* [MAX98357A Amp] */
max_x = 18;
max_y = 19;
max_z = 2;
terminal_h = 10;

/* [Real Time Clock] */
// Real time Clock X
rtc_x= 35;
// Real time Clock Y
rtc_y = 22;
// Real time clock Z
rtc_z = 6.5;

/* [SD Card Reader] */
sd_x = 42;
sd_y = 24; 
sd_z = 2;
sd_card_clearance = 4.5;

/* [Pi Pico] */
// Pico X Dimensions
pico_x = 51.5;
// Pico Y Dimensions
pico_y = 21; 


/* [Settings Buttons] */
set_body_z = 32.5;
set_body_d = 12;
set_button_z = 3;
set_flange_z = 6.5;
set_flange_d = 19;
set_button_d = 12;
set_contact_x = 3;
set_contact_z = 6;


/* [Announcement Button] */
ann_body_z=29.5;
ann_body_d=30;
ann_button_z=3.5;
ann_flange_z=3;
ann_flange_d=33.3;
ann_button_d=24;
ann_contact_x=3;
ann_contact_z=9.5;

/* [Hidden] */

// convenience array Length, Depth, Height
case_size = [case_x, case_y, case_z];

// top of foot width
foot_x = (case_size[0]-usableDiv(maxDiv(case_size, finger))[0]*finger)/2;
foot_h = 8;
foot_ratio = .8;

/* component Locations */

// USB port location from center X 
usb_port_loc_x = -case_size[0]/2 + usb_port_x/2 + material + 8;
usb_port_loc_z = -case_size[2]/2 + usb_port_z/2 + material *2;
// patch the gap in the fingers under the USB port from the edge
usb_finger_patch_x = ceil(abs(usb_port_loc_x/2)/finger) * 5; 
// location of the patch starting with first negative cut
usb_finger_patch_loc_x = -(case_size[0]/2 - usb_finger_patch_x/2 - foot_x);

// pi pico location
pico_x_loc = -usb_port_loc_x;
pico_y_loc = case_size[1]/2 - 51.5/2 - material;
pico_z_loc = material/2 + 1 + material;
pico_rot = [0, 0, 90];
pico_plate = [pico_x, pico_y, material];

// speaker location
// speaker_loc_x = -1*(case_size[0]/2) + speaker_dim[1]/2 + material*2;
speaker_loc_x = -(case_size[0]/2 - cone_dia/2 - material*2);
speaker_loc_y = 0; // + speaker_dim[0]/2 + material*1.5 + ear_od;
speaker_loc_z = cone_height + material/2;
// speaker_loc_z =  speaker_dim[2]/2 + material/2;
// speaker_rot = [0, 0, 90];

speaker_rot = [180, 0, 0];


// realtime clock location
rtc_loc_x = case_size[0]/2 - rtc_x/2 - material*1.5;
rtc_loc_y = -1*(case_size[1]/2 - rtc_z/2 - material*2 +rtc_z/2 );
rtc_loc_z = rtc_y/2 + material;
rtc_rot = [90, 0, 180];
rtc_plate = [rtc_x+material/2, rtc_y+material/2, material];

// sd card reader location
sd_card_loc_x = -case_size[0]/2 + sd_x/2;
sd_card_loc_y = case_size[1]/2 - material * 2 - sd_z/2;
// sd_card_loc_z = material/2 + sd_y/2 + material;
// sd_card_loc_z = sd_y/2 + material*1.5;
sd_card_loc_z = case_size[2]/2 - sd_y/2 - material * 2;
sd_card_rot = [90, -0, 0];
sd_card_plate = [sd_x+material/2 - material, sd_y+material/2, material];

// MAX Amplifier location
max_x_loc = case_size[0]/2 - max_x/2 - 2*material;
max_y_loc = -pico_y_loc/2 - max_y/2;
max_z_loc = material *1.5 + max_z/2;
max_rot = [0, 0, 0];
max_plate = [max_x+material/2, max_y+material/2, material];

// plus and minus set button locations
pb_loc_x = -(case_size[0]/2 - material*2 - set_flange_d/2) +material;
pb_loc_y = case_size[1]/2;
pb_loc_z = case_size[2]/2 - material*2 -set_flange_d/2;
pb_rot = [-90, 0, 0];

// mb_loc_x = -(case_size[0]/2 - material*2 - set_flange_d*1.75);
mb_loc_x = pb_loc_x + set_flange_d*1.25;
mb_loc_y = pb_loc_y;
mb_loc_z = pb_loc_z;


// announcement button location
ann_loc_x = 0;
ann_loc_y = -case_size[1]/4;
ann_loc_z = case_size[2] - material/2;
ann_rot = [0, 0, 0];


// catch dimensions and locations
// length
catch_l = case_size[1] - material*3;

catch_loc_x = case_size[0]/2-material;
catch_loc_y = 0;
catch_loc_z = case_size[2]/2 - 2.5 * material;
catch_rot = [0, 0, -90];
catch_n_fingers = 3;
catch_n_fasteners = 2;
catch_fastener_d = 3;
catch_hole_d = 3.2;
catch_finger_clearance = .1;
catch_bolt_loc_x = catch_loc_x - (nut_plate_width(fastener_d=catch_fastener_d, clearance=.1))/2;

// epsilon to protect against div by zero
eps = 0.0001;

module multiline_text(lines, size=5, line_spacing=1.2, font="Helvetica") {
    color("white")
    for (i = [0 : len(lines) - 1]) {
        translate([0, -i * size * line_spacing]) {
            text(lines[i], size=size, halign="left", valign="baseline");
        }
    }
}
module mount_plate(dim=[5, 10, material], r=.5, color="red" ) {
    color(color) {
            chamfer_square(dim=dim, r=r, center=true);
        }
}


module usb_port(dim, r,) {
    module port_aperature() {
        union() {
            chamfer_square(dim=dim, r=r, center=true);
            translate([0, -(dim[1]/2 -r)]) {
                square([dim[0], r*2], center=true);
            }
        }
    }
    port_aperature();
}

// !usb_port([usb_port_x, usb_port_z], 1);

module foot(w=5, h=8, ratio=.8, center=false) {
    //make a single foot
    q = w - w*(1-ratio);

    trans_coord = center ? [-w/2, -h/2] : [0, 0, 0];
    
    coords = [[0, 0], [w, 0], 
              [q, h], [0, h]];
    translate(trans_coord) 
        polygon(coords);
    
}

module feet() {
    translate([-(case_size[0]/2-foot_x/2), -(case_size[2]/2+foot_h/2), 0]) 
        rotate([180, 0, 0])
        foot(foot_x, foot_h, foot_ratio, true);
    translate([(case_size[0]/2-foot_x/2), -(case_size[2]/2+foot_h/2), 0]) 
        rotate([180, 180, 0])
        foot(foot_x, foot_h, foot_ratio, true);
}


module base(print=false) {
    difference() {
        faceB(size=case_size, finger=finger, lidFinger=finger, material=material, 0);
        // translate([-usb_finger_patch_loc_x, -(case_size[1]/2-material/2)]) {
        //     square([usb_finger_patch_x, material], center=true);
        // }
        translate([speaker_loc_x, -speaker_loc_y]) {
            rotate([0, 0, 90])
            // cutter_square(x=speaker_dim[0], y=speaker_dim[1]);
            cutter_circle(d=cone_dia*.9);
        }
        if(print) {
            translate([-case_size[0]/2 + material*1.5, -case_size[1]/2 + 8 + material * 1.5]){
                multiline_text(["Talking Clock", "github.com/txoof/talking_clock"], size=4);
            }
        }
    }

 
}

module left() {
    sd_card_cutout = [sd_card_clearance, sd_y + material/2];
    difference() {
        faceC(size=case_size, finger=finger, lidFinger=finger, material=material);
        translate([-sd_card_loc_y + sd_z/2, -sd_card_loc_z]) {
            chamfer_square(dim=sd_card_cutout, r = .5, center=true);
        }

        translate([catch_loc_y, catch_loc_z]) {
            finger_slot_cutter(length=catch_l, material=material, finger_width=finger,
                            n_fingers=catch_n_fingers, slot_clearance=catch_finger_clearance);
        }        
    }
}

// !left();


 module right() {
    difference() {
        faceC(size=case_size, finger=finger, lidFinger=finger, material=material);
        translate([catch_loc_y, catch_loc_z]) {
            finger_slot_cutter(length=catch_l, material=material, finger_width=finger,
                            n_fingers=catch_n_fingers, slot_clearance=catch_finger_clearance);
        }
    }
 }
 
// !right();

 module front() {
    union() {
        difference() {
            faceA(size=case_size, finger=finger, lidFinger=finger, material=material);
        }
    feet();
    }
 }




 module back() {
    text_size = 10;
    valign = "center";
    halign = "center";

    union() {
        difference() {
            faceA(size=case_size, finger=finger, lidFinger=finger, material=material);
            translate([usb_port_loc_x, usb_port_loc_z, 0]) {
                usb_port([usb_port_x, usb_port_z], 2);
            }
            translate([pb_loc_x, pb_loc_z]) {
                arcade_button_cutter(body_d=set_body_d);
            }
            translate([mb_loc_x, mb_loc_z]) {
                arcade_button_cutter(body_d=set_body_d);
            }
    
            translate([pb_loc_x, pb_loc_z - set_flange_d/2 - text_size/1.5]) {
                text(text="+", font=font, 
                        size=text_size,
                        valign=valign,
                        halign=halign);
            }
            translate([mb_loc_x, mb_loc_z - set_flange_d/2 - text_size/1.5]) {
                text(text="–", font=font, 
                        size=text_size,
                        valign=valign,
                        halign=halign);
            }


        
        }

        feet();
    }
 }

// !back(label=true);

 module top() {
    difference() {
        faceB(size=case_size, finger=finger, lidFinger=finger, material=material);
        translate([ann_loc_x, ann_loc_y]) {
            arcade_button_cutter(ann_body_d);
        }
        for (i = [-1, 1]) {
            translate([i*catch_bolt_loc_x, 0]) {
                rotate(catch_rot){
                    bolt_hole_slot_cutter(length=catch_l,
                                        n_fasteners=catch_n_fasteners,
                                        hole_d=catch_hole_d,
                                        hole_clearance=0);
                }
            }
        }
    }
 }

// !top();

 module layout(three_dimensional=true) {
  if (three_dimensional) {
//    colors=["green", "blue", "darkblue", "red", "darkred", "brown"];
    colors=["BurlyWood", "Wheat", "Wheat", "Goldenrod", "Goldenrod", "BurlyWood"];
      
    // Base 0
    color(colors[0]) translate([0, 0, 0])
        rotate([180, 0, 0]) {
            linear_extrude(height=material, center=true)
            children(0);
        }
    
    // Left 1
    color(colors[1]) 
      translate([-case_size[0]/2+material/2, 0, case_size[2]/2-material/2]) 
      rotate([90, 0, -90])
        linear_extrude(height=material, center=true)
        children(1);
    
    // Right 2
    color(colors[2])
      translate([case_size[0]/2-material/2, 0, case_size[2]/2-material/2])
      rotate([90, 0, -90]) {
        linear_extrude(height=material, center=true)
        children(2);
      }

    // // Front 3
    // color(colors[3]) 
    //   translate([0, -case_size[1]/2+material/2, case_size[2]/2-material/2])
    //   rotate([90, 0, 0])
    //     linear_extrude(height=material, center=true)
    //     children(3);

    //  Back 4
    color(colors[4])
        translate([0, case_size[1]/2-material/2, case_size[2]/2-material/2])
            rotate([90, 0, 180]) {
                linear_extrude(height=material, center=true)
                children(4);
            }
    
    // Lid 5
    color(colors[5])
        translate([0, 0, case_size[2]-material]) {
            linear_extrude(height=material, center=true)
            children(5);
        }
  


    translate([pico_x_loc, pico_y_loc, pico_z_loc]) {
        rotate(pico_rot) {
            pi_pico();
        }
    }
    

    translate([speaker_loc_x, speaker_loc_y, speaker_loc_z]) {
        rotate(speaker_rot) {
            // box_speaker(dim=speaker_dim, ears=ears, od=ear_od, h=ear_h);
            cone_speaker(dia=cone_dia, magnetDia=cone_magnet_dia, height=cone_height);

        }
    }


    translate([rtc_loc_x, rtc_loc_y, rtc_loc_z]) {
        rotate(rtc_rot) {
            rtc(dim=[rtc_x, rtc_y, rtc_z]);
        }
    }

    translate([rtc_loc_x, rtc_loc_y, rtc_loc_z]){
        color("pink")
        rotate([90, 0, 0]){
            linear_extrude(h=material) {
                mount_plate(rtc_plate);
            }
        }
    }

    translate([pico_x_loc, pico_y_loc, pico_z_loc - material -1]) {
        color("purple")
        rotate(pico_rot) {
            linear_extrude(h=material)
                mount_plate(pico_plate);
        }
    }

    // hack to render the sd_card
    sd_loc_z_render = sd_y/2 + material*1.5;

    translate([sd_card_loc_x, sd_card_loc_y, sd_loc_z_render]) {
        rotate(sd_card_rot) {
            sd_card_reader(dim=[sd_x, sd_y, sd_z]);
        }
    }
    translate([sd_card_loc_x+material, sd_card_loc_y+material + sd_z/2, sd_loc_z_render]) {
        color("orange")
        rotate(sd_card_rot)
            linear_extrude(h=material) {
                mount_plate(sd_card_plate);
        }
    }



    translate([max_x_loc, max_y_loc, max_z_loc]) {
        rotate(max_rot) {
            max_amp([max_x, max_y, max_z], terminal_h);
        }
    }

    translate([max_x_loc, max_y_loc, max_z_loc - max_z/2 -material]) {
        color("silver")
        rotate(max_rot){
            linear_extrude(h=material){
                mount_plate(max_plate);
            }
        }
    }


    // setting button (plus)
    translate([-pb_loc_x, pb_loc_y, case_size[2]/2 + material*2]) {
        color("red") {
            rotate(pb_rot) {
                arcade_button(body_z=set_body_z,
                body_d=set_body_d,
                button_z=set_button_z,
                flange_z=set_flange_z,
                flange_d=set_flange_d,
                button_d=set_button_d,
                contact_x=set_contact_x,
                contact_z=set_contact_z);
            }
        }

    }

    // setting button (minus)
    translate([-mb_loc_x, mb_loc_y, case_size[2]/2 + material*2]) {
        color("darkgray") {
            rotate(pb_rot) {
                arcade_button(body_z=set_body_z,
                body_d=set_body_d,
                button_z=set_button_z,
                flange_z=set_flange_z,
                flange_d=set_flange_d,
                button_d=set_button_d,
                contact_x=set_contact_x,
                contact_z=set_contact_z);
            }
        }

    }

    // announcement button
    translate([ann_loc_x, ann_loc_y, ann_loc_z]) {
        color("CornSilk") {
            rotate(ann_rot) {
                arcade_button(body_z=ann_body_z,
                              body_d=ann_body_d,
                              button_z=ann_button_z,
                              flange_z=ann_flange_z,
                              flange_d=ann_flange_d,
                              contact_z = ann_contact_z);
            }
        }
    }

    // hack for catch z location in render
    catch_loc_z_render = case_size[2] - material * 3;

    for (i = [-1, 1]) {
        translate([i*catch_loc_x, catch_loc_y, catch_loc_z_render]) {
            rotate([catch_rot[0], catch_rot[1], i*catch_rot[2]]) {
                nut_sandwich_3d(
                length=catch_l,
                finger_width=finger,
                material=material,
                n_fasteners=catch_n_fasteners,
                fastener_d=catch_fastener_d,
                hole_d=catch_hole_d,
                plate_thickness=material,
                middle_thickness=material,
                show_bolts=1,
                );
            }
        }
    }



  } else {
    //   Reference square 20x10
    color("black")
    translate([case_size[0]/2 + material + 10, 
               -(case_size[1]/2 + material + 5)])
    square([20, 10], center = true);

    // SD Card Mounting Plate 
    color("orange") 
        translate([-case_size[0]/2 - sd_card_plate[1]/2 - material, 
                    case_size[1] + sd_card_plate[0]/2 + material*2])
        rotate([0, 0, 90])
        mount_plate(sd_card_plate);
    
    // RTC mounting Plate
     color("pink") 
        translate([-case_size[0]/2 - sd_card_plate[1]/2 - rtc_plate[1]- material *2, 
                   case_size[1] + sd_card_plate[0]/2 + 2 * material])
        rotate([0, 0, 90])
        mount_plate(rtc_plate);

    // Pi Pico Mounting Plate
    color("purple")
        translate([-case_size[0]/2 - pico_plate[1]/2 - material, 
                  case_size[1] + sd_card_plate[0]/2 + pico_plate[0]+ 2 * material])
        rotate([0, 0, 90])
        mount_plate(pico_plate);
    
    nut_plate_x = case_size[0]/2 + nut_plate_width(fastener_d=catch_fastener_d)*3;
    nut_plate_y = case_size[1] + material;
    for (i = [0, 1]) {
        color("aqua") {
            translate([nut_plate_x, 
                    i*nut_plate_y]) {
                rotate([0, 0, 90]) {
                    nut_sandwich_layout(length=catch_l,
                                        finger_width=finger,
                                        material=material,
                                        n_fasteners=catch_n_fasteners,
                                        n_fingers=catch_n_fingers,
                                        fastener_d=catch_fastener_d,
                                        hole_d=catch_hole_d);
                }
            }
        }
    }

      color("green") translate([0, 0, 0])
        rotate([0, 180, 0])
        children(0);
      
      color("blue") translate([-(case_size[0]/2+case_size[2]/2+material), -(case_size[1]/2+material), 0])
        rotate([0, 0, 90])
        children(1);
      
      color("darkblue") translate([-(case_size[0]/2+case_size[2]/2+material), case_size[1]/2+material, 0])
        rotate([0, 0, 90])
        children(2);
      
     color("red") translate([0, -(case_size[1]/2+case_size[2]/2+material), 0])
        rotate([0, 0, 0])
        children(3);
      
     color("darkred") translate([0, case_size[1]*1.5+case_size[2]/2+material+foot_h, 0])
        children(4);
      
     color("brown") translate([0, case_size[1] + material, 0]) 
        children(5);
  }

}



layout(three_dimensional=three_d) {
    base();
    left();
    right();
    front();
    back();
    top();
}