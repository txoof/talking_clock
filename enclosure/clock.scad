use <./scad_libraries/finger_joint_box.scad>
use <./scad_libraries/voronoi.scad>
use<./scad_libraries/arcade_button.scad>
use<./scad_libraries/cone_speaker.scad>
use<./scad_libraries/potentiometer.scad>


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
clockY=100;
// External Z
clockZ=60;

/* [Components] */
// speaker diameter
speakerDia = 40;
// speaker total Z height
speakerHeight = 18;
// X position (internal) from center
speakerXpos = 0;
// Z position (internal) from center
speakerZpos = 0;

// Switch X position (on lid) from center
switchX = 0;
// Switch Y position (on lid) from center
switchY = 0;

// USB Connector Overmolding X 
usbOverX = 15;
// USB Connector Overmolding Y
usbOverY = 9;

// Potentiometer 
potXpos = clockX/3 *2;
potZpos = clockZ/3 *2;
potBodyDim = [10, 12, 8.4];
potBushingDia = 9;
potBushingLen = 5;


/* [Look and Feel] */
//radius of chamfers for curved edges
chamfer_r = 2; //[0:.1:3]
//voronoi void roudness
vor_round=1;//[0.01:.01:1.5]
//voronoi wall thickness
vor_thick=.8;//[0.25:0.01:2]
//border at edge 
vor_border=(6+material)*2;

//cutout border to use around all IO ports
cutout_border = 4.5;//[0:.1:10]

/* [Hidden] */
caseSize = [clockX, clockY, clockZ];

// patch this many fingers for the USB port
// usbPortFingerPatch = (((usbOverX + 2 * cutout_border) % finger) + 2) * finger;
usbPortFingerPatch = (floor((usbOverX + 2 * cutout_border) / finger) + ((usbOverX + 2 * cutout_border) % finger > 0 ? 2 : 0)) * finger;
echo(usbPortFingerPatch);



// feet for the case
foot_x = (caseSize[0]-usableDiv(maxDiv(caseSize, finger))[0]*finger)/2;
foot_ratio = .5;
foot_h = 8;

// Mounting Holes
mountingHole = 2.9;


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

module port(dim, border=cutout_border, r=chamfer_r, cutter=false) {
    // make a port that can be located at the edge of the enclosure
    outerDim = [dim[0] + cutout_border * 2, dim[1] + cutout_border];
    difference() {
        union() {
            chamfer_square(dim=outerDim, r=chamfer_r * 1.5);
            square([outerDim[0], chamfer_r]);
        }
        
        if (!cutter) {
            union() {
                translate([cutout_border, 0, 0]) {
                    chamfer_square(dim=dim, r=chamfer_r);
                    square([dim[0], chamfer_r]);
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
        translate([clockX/2 - usbPortFingerPatch - material, clockY/2 - material, 0])
                square([usbPortFingerPatch, material]);    
    }

}
// !base();

module left() {
    difference() {
        // echo("SD Card Slot height: ", sdCard_d[2]*zMult);
        faceC(caseSize, finger, lidFinger, material);
        my_random_voronoi(caseSize[1]-vor_border, caseSize[2]-vor_border, n=30, round=vor_round, thickness=vor_thick, center=true);
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
             my_random_voronoi(caseSize[1]-vor_border, caseSize[2]-vor_border, n=30, round=vor_round, thickness=vor_thick, center=true);
 
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
            my_random_voronoi(caseSize[0]-vor_border, caseSize[2]-vor_border, n=50, round=vor_round, thickness=vor_thick, center=true);
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
   

            translate([clockX/2 - (usbOverX + cutout_border *2 ) - material - 3, - clockZ/2 + material, 0]) {
                port(dim=[usbOverX, usbOverY], r=chamfer_r, cutter=true);
            }
            // translate([clockX/2 - potXpos, clockZ/2 - potZpos, 0]) {
            //     potentiometer_cutter(bushing_dia=9, shaft_dia=6);
            // }

        }
        // # patch the finger joints
        // color("red")
        translate([clockX/2 - usbPortFingerPatch/2 - foot_x, - clockZ/2 + material/2, 0]) {
            square([usbPortFingerPatch, material,], center=true);
        }


        translate([clockX/2 - (usbOverX + cutout_border *2 ) - material - 3, - clockZ/2 + material, 0]) {
            port(dim=[usbOverX, usbOverY], r=chamfer_r);
        }
        
        //add some feet
        feet();

    }


}

// !back();

module lid() {
    union() { 
        difference() { // difference the lid from the voronoi
            faceB(caseSize, finger, lidFinger, material, 0, lid=true);
            arcadeSwitchCutter();
            // my_random_voronoi(caseSize[0]-vor_border, caseSize[1]-vor_border, n=100, round=vor_round, thickness=vor_thick, center=true);
            
        } 
    }
}

module layout(threeD=true) {
  if (threeD) {
 //   colors=["green", "blue", "darkblue", "red", "darkred", "brown"];
    colors=["BurlyWood", "Wheat", "Wheat", "Goldenrod", "Goldenrod", "BurlyWood", "Blue"];
      
    color(colors[0]) translate([0, 0, 0])
        linear_extrude(height=material, center=true)
        children(0);
    
    color(colors[1]) 
      translate([-caseSize[0]/2+material/2, 0, caseSize[2]/2-material/2]) 
      rotate([90, 0, -90])
        linear_extrude(height=material, center=true)
        children(1);
     
    color(colors[2])
      translate([caseSize[0]/2-material/2, 0, caseSize[2]/2-material/2])
      rotate([90, 0, -90])
        linear_extrude(height=material, center=true)
        children(2);


    color("Blue") 
      translate([0, -caseSize[1]/2+material/2, caseSize[2]/2-material/2])
      rotate([90, 0, 0])
        linear_extrude(height=material, center=true)
        children(3);
        
    color(colors[4])
        translate([0, caseSize[1]/2-material/2, caseSize[2]/2-material/2])
            rotate([90, 0, 0])
                linear_extrude(height=material, center=true)
                children(4);
    
    // color(colors[5])
    //     translate([0, 0, caseSize[2]-material])
    //         rotate([0, 0, 0])
    //             linear_extrude(height=material, center=true)
    //             children(5);
    
    translate([speakerXpos, -clockY/2 + speakerHeight + material, speakerDia/2 + material]){
        rotate([90, 0, 0])
        // speaker(dia=speakerDia, height=speakerHeight);
        speaker();
    }

    
    // translate([clockX/2 - potXpos, clockY/2 - material - potBodyDim[2]/2, clockZ-potZpos - material/2]) {
    //     rotate([-90, 0, 0]) {
    //         color("gray")
    //         potentiometer(body_dim=potBodyDim, bushing_dia=potBushingDia, bushing_len=potBushingLen);
    //     }
    // }

    translate([switchX, switchY , clockZ - material/2]) {
        arcadeSwitch();
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
