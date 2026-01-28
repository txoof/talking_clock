// Simple speaker driver
// Usage: speaker(); or speaker(dia=50, height=20);

module speaker(dia=40, height=18) {
    $fn = 64;
    
    // Dimensions
    magnetDia = dia * 0.75;
    magnetHeight = height * 0.5;
    
    coneDia = dia * 0.9;
    coneTopDia = dia * 0.3;
    coneHeight = height * 0.5;
    
    flangeHeight = 2;
    
    color("DarkGray")
    union() {
        // Magnet
        cylinder(d=magnetDia, h=magnetHeight);

        // Cone
        translate([0, 0, magnetHeight])
            difference() {
                union() {
                cylinder(d=coneDia, h=coneHeight);
                // Flange
                translate([0, 0, coneHeight - flangeHeight])
                    cylinder(d=dia, h=flangeHeight);
                }
                cylinder(d2=coneDia, d1=coneTopDia, h=coneHeight+0.1);

            }

    }
}

// speaker();