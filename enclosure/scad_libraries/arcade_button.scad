module arcadeSwitch() { 
    $fn = 64;

    // Dimensions
    // Total switch height: 41.9
    // Internal clearance required: 35.5
    buttonDia = 25;
    flangeDia = 33.2;
    flangeHeight = 3;
    buttonHeight = 3.4 + flangeHeight;
    nutZ = 11;
    nutDia = 36;

    threadDia = 29.5;
    threadLength = 17;

    contactWidth = 4.8;
    contactThickness = 0.5;
    contactHeight = 10;
    contactSpacing = 8;


    bodyDia = threadDia / 2;
    totalBodyHeight = 18.5;
    bodyHeight = totalBodyHeight - contactHeight;


  color("Gold")
  union() {
    // Button (extends above flange)
    cylinder(h=buttonHeight, d=buttonDia);
    
    // Flange
    cylinder(h=flangeHeight, d=flangeDia);

    // Thread
    translate([0, 0, -threadLength])
    cylinder(h=threadLength, d=threadDia);
        
    // Body
    translate([0, 0, -(threadLength + bodyHeight)])
    cylinder(h=bodyHeight, d=bodyDia);
    // translate([0, 0, flangeTopZ - flangeHeight - bodyHeight - threadLength])
    //   cylinder(d=threadDia, h=threadLength, $fn=36);
    
    // Contacts (two blade connectors)
    // baseZ = flangeTopZ - flangeHeight - bodyHeight - threadLength;
    // translate([-contactSpacing/2, -contactThickness/2, baseZ - contactHeight])
    translate([-contactWidth/2, contactSpacing/2, -(threadLength + bodyHeight + contactHeight)])
      cube([contactWidth, contactThickness, contactHeight]);
    
    translate([-contactWidth/2, -contactSpacing/2, -(threadLength + bodyHeight + contactHeight)])
      cube([contactWidth, contactThickness, contactHeight]);
  }
}

module arcadeSwitchCutter() {
    $fn = 128;
    threadDia = 29.5;
    overage = 0.5;
    circle(d=threadDia + overage);
}

// arcadeSwitch();
// arcadeSwitchCutter();