// 6x6 tactile switch
// Usage: tactileSwitch(); or tactileSwitch(buttonHeight=3.5);

module tactileSwitch(bodyWidth=6, bodyHeight=3.4, buttonHeight=0.9, terminals=true) {
    $fn = 36;
    
    // Dimensions   
    buttonDia = 3.5;
    
    pinWidth = 0.5;
    pinLength = 3.5;
    pinSpacing = 4.5; // center to center
    
    color("DarkGray")
    union() {
        // Body
        translate([-bodyWidth/2, -bodyWidth/2, 0])
            cube([bodyWidth, bodyWidth, bodyHeight]);
        
        // Button
        translate([0, 0, bodyHeight])
            cylinder(d=buttonDia, h=buttonHeight);
        
        // Pins (4 corners)
        if (terminals) {
            translate([pinSpacing/2, pinSpacing/2, -pinLength])
                cube([pinWidth, pinWidth, pinLength]);
            
            translate([-pinSpacing/2 - pinWidth, pinSpacing/2, -pinLength])
                cube([pinWidth, pinWidth, pinLength]);
            
            translate([pinSpacing/2, -pinSpacing/2 - pinWidth, -pinLength])
                cube([pinWidth, pinWidth, pinLength]);
            
            translate([-pinSpacing/2 - pinWidth, -pinSpacing/2 - pinWidth, -pinLength])
                cube([pinWidth, pinWidth, pinLength]);
        }
    }
}

