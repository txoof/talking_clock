use <./scad_libraries/finger_joint_box.scad>
use <./scad_libraries/voronoi.scad>
use<./scad_libraries/arcade_button.scad>
use<./scad_libraries/cone_speaker.scad>
use<./scad_libraries/potentiometer.scad>
use<./scad_libraries/speaker_grill.scad>


/*[Project Setup]*/
// VERSION="Clock V0.0";
// False: SVG layout, True: 3D Visualization
ThreeD = true;


/* [Material and Design] */
// average material thickness in mm
material = 4.0;
//overage buffer to add to the internal dimensions of the case
over = 10;
//finger joint width in mm
finger = 5; 
//finger joint width for the lid
lidFinger = finger;

/* [Dimensions] */
// External X
clockX=100;
// External Y
clockY=75;
// External Z
clockZ=55;

/* [Speaker] */
// speaker diameter
speakerDia = 37.8;
// speaker magnet diameter
magnetDia = 22;
// speaker total Z height
speakerHeight = 25;
// Speaker X position (from center)
speakerXpos = clockX/-2 + speakerDia/2 + material*1.5;
// Speaker Y position (from center)
speakerYpos = 0;

/* [Set Button] */
// announcement button X
buttonX = 25;
// announcement button Y
buttonY = 10;

/* [Announcement Button] */
// Switch X position (on lid) from center
switchX = 0;
// Switch Y position (on lid) from center
switchY = 0;

/* [USB Connector with Over Molding] */
// USB Connector Overmolding X 
usbOverX = 15;
// USB Connector Overmolding Y
usbOverY = 9;


// Real time Clock X
rtcX = 35;
// Real time Clock Y
rtcY = 22;
// Real time clock Z
rtcZ = 6.5;

// MAX98357A Amp X
maxX = 18;
// MAX98357A Amp Y
maxY = 19;
// MAX98357A Amp Z
maxZ = 10;

// SD Card Reader X
sdRX = 42;
// SD Card Reader Y
sdRY = 24;
// SD Card port Clearance (z min)
sdRClearance = 3.5;

/* [Pi Pico] */
// Pico X Dimensions
picoX = 51.5;
// Pico Y Dimensions
picoY = 21;
// Pico X Position (from center)
// Pico Y Position (from center)



/* [Look and Feel] */
//radius of chamfers for curved edges
chamfer_r = 2; //[0:.1:3]
//voronoi void roudness
// vor_round=1;//[0.01:.01:1.5]
// //voronoi wall thickness
// vor_thick=.8;//[0.25:0.01:2]
//cutout border to use around all IO ports
cutout_border = 4;//[0:.1:10]

/* [Hidden] */
caseSize = [clockX, clockY, clockZ];

// //border at edge 
// vor_border=(6+material)*2;

// border around port
border = (material)*4;

speakerZpos = 0;

// patch this many fingers for the USB port
// usbPortFingerPatch = (((usbOverX + 2 * cutout_border) % finger) + 2) * finger;
usbPortFingerPatch = (floor((usbOverX + 2 * cutout_border) / finger) + ((usbOverX + 2 * cutout_border) % finger > 0 ? 2 : 0)) * finger;

// Dupont Pin - 90 Degree
pin90len = 5;
// Dupont pin center-to-center
pinPitch = 2.54;
// Dupont pin thickness
pinThick = 0.64;



// feet for the case
foot_x = (caseSize[0]-usableDiv(maxDiv(caseSize, finger))[0]*finger)/2;
foot_ratio = .5;
foot_h = 8;

// // Mounting Holes
// mountingHole = 2.9;

module dupont_pins(count=4, pinPitch=2.54, pinThick=0.64, pin90len=6) {
    y0 = -((count - 1) * pinPitch) / 2;

    for (i = [0 : count - 1]) {
        translate([0, y0 + i * pinPitch, 0]) {
            cube([pin90len + 4, pinThick, pinThick], center=true);
        }
    }
}

module rtc() {
    color("blue") {
        cube([rtcX, rtcY, rtcZ], center=true);
    }
    
    color("gold") {
        translate([rtcX / 2 + pin90len / 2, 0, rtcZ / 2 + pinThick / 2]) {
            dupont_pins(
                count=4,
                pinPitch=pinPitch,
                pinThick=pinThick,
                pin90len=pin90len
            );
        }
    }

    color("white") {
        translate([0, 0, rtcZ / 2]) {
            linear_extrude(height=0.4) {
                text("RTC", size=3, halign="center", valign="center");
            }
        }
    }
}

module maxAmp() {
    color("red") {
        cube([maxX, maxY, 2], center=true);
    }

    color("gold") {
        translate([maxX/2 - pinThick*1.5, 0, pin90len]) {
            rotate([0, 90, 0])
            dupont_pins(
                count=6,
                pinPitch=pinPitch,
                pinThick=pinThick,
                pin90len=pin90len
            );
        }
    }

    color("white") {
        translate([0, 0, 2 / 2]) {
            linear_extrude(height=0.4) {
                text("MAXAmp", size=3, halign="center", valign="center");
            }
        }
    }



}

module piPico() {
    color("Yellow") {
        cube([picoX, picoY, 2], center=true);
    }

    color("gold") {
        translate([0, picoY/2 - pinThick*1.5, pin90len]) {
            rotate([90, 90, 0])
            dupont_pins(
                count=20,
                pinPitch=pinPitch,
                pinThick=pinThick,
                pin90len=pin90len
            );
        }
        translate([0, -picoY/2 + pinThick*1.5, pin90len]) {
            rotate([90, 90, 0])
            dupont_pins(
                count=20,
                pinPitch=pinPitch,
                pinThick=pinThick,
                pin90len=pin90len
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

module sdCardReader() {
    color("green") {
        cube([sdRX, sdRY, 2], center=true);
    }

    color("gold") {
        translate([sdRX / 2 + pin90len / 2, 0, 1 + pinThick / 2]) {
            dupont_pins(
                count=6,
                pinPitch=pinPitch,
                pinThick=pinThick,
                pin90len=pin90len
            );
        }
    }
    
    color("white") {
        translate([0, 0, 2 / 2]) {
            linear_extrude(height=0.4) {
                text("SD Card Reader", size=3, halign="center", valign="center");
            }
        }
    }      
}


module foot(w, h, ratio, center=false) {
    //make a curved foot
    q = w - w*(1-ratio);

    trans_coord = center ? [-w/2, -h/2] : [0, 0, 0];
    
    coords = [[0, 0], [w, 0], 
              [q, h], [0, h]];
    translate(trans_coord) 
        polygon(coords);
    
}



module feet() {
    translate([-(caseSize[0]/2-foot_x/2), -(caseSize[2]/2+foot_h/2), 0]) 
        rotate([180, 0, 0])
        foot(foot_x, foot_h, foot_ratio, true);
    translate([(caseSize[0]/2-foot_x/2), -(caseSize[2]/2+foot_h/2), 0]) 
        rotate([180, 180, 0])
        foot(foot_x, foot_h, foot_ratio, true);
}


module chamfer_square(dim, r, center=false, fn=32) {
    $fn=fn;
    myDim = [dim[0]-r*2, dim[1]-r*2];
    trans_coord = center ? [-myDim[0]/2, - myDim[1]/2, 0] : [r, r, 0];
    translate(trans_coord)
    minkowski() {
        circle(r);
        square(myDim);
    }
}

module port(dim, border=cutout_border, r=chamfer_r, outer_r=chamfer_r, cutter=false) {
    // make a port that can be located at the edge of the enclosure
    outerDim = [dim[0] + cutout_border * 2, dim[1] + cutout_border];
    difference() {
        union() {
            chamfer_square(dim=outerDim, r=outer_r * 1.5);
            square([outerDim[0], outer_r*1.2]);
        }
        
        if (!cutter) {
            union() {
                translate([cutout_border, 0, 0]) {
                    chamfer_square(dim=dim, r=r);
                    square([dim[0], r]);
                }
            }
        }
    }
}


// module roundCutout(x=10, y=5, border=cutout_border, r=chamfer_r, rounded=true, center=false, fn=64) {
//     outerDim = [x + cutout_border *2, y + cutout_border * 2];

//     cornerRad = rounded ? r : 0.001;

//     translate(center ? [0, 0, 0] : [outerDim[0]/2, outerDim[1]/2, 0] )
//     difference() {
//         chamfer_square(dim=outerDim, r=r, fn=fn, center=true);
//         chamfer_square(dim=[x, y], r=cornerRad, fn=fn, center=true);
//     }

// }
// // !roundCutout(center=true, );



module base() {
    difference() {
        faceB(caseSize, finger, finger, material, 0);
    
        color("red")
        translate([clockX/2 - usbPortFingerPatch - material, clockY/2 - material, 0]) {
                square([usbPortFingerPatch, material]); 
        }
        translate([speakerXpos, speakerYpos, 0]) {
            cutter_circle(d=speakerDia);        
        }
    }
}


module left() {
    difference() {
        // echo("SD Card Slot height: ", sdCard_d[2]*zMult);
        faceC(caseSize, finger, lidFinger, material);
        // my_random_voronoi(caseSize[1]-vor_border, caseSize[2]-vor_border, n=30, round=vor_round, thickness=vor_thick, center=true);
        // remove a slot for sd card access
        // translate([0, -caseSize[2]/2 + (sdCard_d[2]*zMult + material)/2 , 0])
        //     chamfer_square([sdCard_d[0], sdCard_d[2]*zMult + material], r=1, center=true);
        
    }
}
// !left();

module right() {
    union() {
        difference() {
            faceC(caseSize, finger, lidFinger, material);
            //  my_random_voronoi(caseSize[1]-vor_border, caseSize[2]-vor_border, n=30, round=vor_round, thickness=vor_thick, center=true);
 
            // cut out space for usb, network port
            //translate([0, -(caseSize[2]-ports_d[2]-material-sdCard_d[2])/2, 0])
            // translate([0, -(caseSize[2]/2-ports_d[2]/2-material), 0])
            //     square([ports_d[0], ports_d[2]], center=true);
            // //cut off the fingers - not needed here
            // translate([0, -(caseSize[2]/2-material/2), 0])
            //     square([caseSize[1], material], center=true);
        }
        //add a bordered region around the port 
//         difference() {
//             translate([0, -(caseSize[2]/2-ports_d[2]/2-material), 0])
//                 square([ports_d[0]+cutout_border, ports_d[2]+cutout_border], center=true);
//             translate([0, -(caseSize[2]/2-ports_d[2]/2-material), 0])
//                 chamfer_square([ports_d[0], ports_d[2]], r=chamfer_r, center=true);
// //                square([ports_d[0], ports_d[2]], center=true);
//             translate([0, -(caseSize[2]/2), 0])
//                 square([caseSize[1], material*2], center=true);
//         }
    }
}

// !right();

module front() {

    union() {
        difference() {
            faceA(caseSize, finger, lidFinger, material, 0);
            // my_random_voronoi(caseSize[0]-vor_border, caseSize[2]-vor_border, n=50, round=vor_round, thickness=vor_thick, center=true);
            // cutter_square(x=caseSize[0]-vor_border, y=caseSize[2]-vor_border,
            //               hole_r=1, gap=.5);

        }
        feet();
    }
}

// !front();

module back() {
    foot_x = (caseSize[0]-usableDiv(maxDiv(caseSize, finger))[0]*finger)/2;
    
    union() {
        difference() {
            faceA(caseSize, finger, lidFinger, material, 0);
            // my_random_voronoi(caseSize[0]-vor_border, caseSize[2]-vor_border, n=50, round=vor_round, thickness=vor_thick, center=true);
   
            // cutter_square(x=caseSize[0]-cutout_border*3, y=caseSize[2]-cutout_border-usbOverY, 
            //               hole_r=2, gap=2, hole_sides=6,
            //               even_rot=30,
            //               odd_rot=30);
            translate([clockX/2 - (usbOverX + cutout_border *2 ) - material - 3, - clockZ/2 + material, 0]) {
                port(dim=[usbOverX, usbOverY], r=chamfer_r, cutter=true);
            }
            chamfer_square(dim=[buttonX, buttonY], r=chamfer_r/2, center=true);
        }
        // # patch the finger joints
        // color("red")
        translate([clockX/2 - usbPortFingerPatch/2 - foot_x, - clockZ/2 + material/2, 0]) {
            square([usbPortFingerPatch, material,], center=true);
        }

        // add the border back to the port
        translate([clockX/2 - (usbOverX + cutout_border *2 ) - material - 3, - clockZ/2 + material, 0]) {
            port(dim=[usbOverX, usbOverY], r=chamfer_r);
        }
        
        //add some feet
        feet();

    }
}


module lid() {
    union() { 
        difference() { // difference the lid from the voronoi
            faceB(caseSize, finger, lidFinger, material, 0, lid=true);
                translate([switchX, switchY, 0]) {
                arcadeSwitchCutter();
            }
            // my_random_voronoi(caseSize[0]-vor_border, caseSize[1]-vor_border, n=100, round=vor_round, thickness=vor_thick, center=true);
            
        } 
    }
}

module layout(threeD=true) {
  if (threeD) {
//    colors=["green", "blue", "darkblue", "red", "darkred", "brown"];
    colors=["BurlyWood", "Wheat", "Wheat", "Goldenrod", "Goldenrod", "BurlyWood"];
      
    // Base 0
    color(colors[0]) translate([0, 0, 0])
        linear_extrude(height=material, center=true)
        children(0);
    
    // Left 1
    color(colors[1]) 
      translate([-caseSize[0]/2+material/2, 0, caseSize[2]/2-material/2]) 
      rotate([90, 0, -90])
        linear_extrude(height=material, center=true)
        children(1);
    
    // Right 2
    color(colors[2])
      translate([caseSize[0]/2-material/2, 0, caseSize[2]/2-material/2])
      rotate([90, 0, -90])
        linear_extrude(height=material, center=true)
        children(2);

    // Front 3
    color(colors[3]) 
      translate([0, -caseSize[1]/2+material/2, caseSize[2]/2-material/2])
      rotate([90, 0, 0])
        linear_extrude(height=material, center=true)
        children(3);

    //  Back 4
    color(colors[4])
        translate([0, caseSize[1]/2-material/2, caseSize[2]/2-material/2])
            rotate([90, 0, 0])
                linear_extrude(height=material, center=true)
                children(4);
    
    // Lid 5
    translate([speakerXpos, speakerYpos, speakerHeight+material]) {
        rotate([180, 0, 0])
        // speaker(dia=speakerDia, height=speakerHeight);
        speaker(dia=speakerDia, magnetDia=magnetDia, height=speakerHeight);
    }

    color("cornsilk")
    translate([switchX, switchY , clockZ - material/2]) {
            arcadeSwitch();
    }



    translate([clockX/2 - picoY/2 - material - usbOverX/2 + cutout_border, clockY/2 - picoX/2 - material, material-1]) {
        rotate([0, 0, 90]) {
            piPico();
        }
    }
  
  } else {
      //Reference square 20x10
      color("black")
      translate([-caseSize[0]/2-material-20, caseSize[1]+20, 0])
        square([20, 10], center = true);
      
      color("green") translate([0, 0, 0])
        rotate([0, 180, 0])
        children(0);
      
      color("blue") translate([-(caseSize[0]/2+caseSize[2]/2+material), -(caseSize[1]/2+material), 0])
        rotate([0, 0, 90])
        children(1);
      
      color("darkblue") translate([-(caseSize[0]/2+caseSize[2]/2+material), caseSize[1]/2+material, 0])
        rotate([0, 0, 90])
        children(2);
      
     color("red") translate([0, -(caseSize[1]/2+caseSize[2]/2+material), 0])
        rotate([0, 0, 0])
        children(3);
      
     color("darkred") translate([0, caseSize[1]*1.5+caseSize[2]/2+material+foot_h, 0])
        children(4);
      
     color("brown") translate([0, caseSize[1] + material, 0]) 
        children(5);
  }

}



layout(threeD=ThreeD) {
    base();
    left();
    right();
    front();
    back();
    lid();
}
