eps = 0.0001;

module arcadeSwitch(body_z=29.5,
                    body_d=30,
                    button_z=3,
                    flange_z=3,
                    flange_d=33.3,
                    button_d=24,
                    contact_x=3,
                    contact_z=9.5,
                    $fn=36) {
  
  displacement_z = -body_z+flange_z+button_z;
  lower_z = body_z-flange_z-button_z;

  color("Gold")
  union() {
    translate([0, 0, displacement_z]) {
      cylinder(body_z, d=button_d);
    }
    translate([0, 0, -lower_z]) {
      cylinder(h=lower_z, d=body_d);
    }
    cylinder(h=flange_z, d=flange_d);
    for (i = [-1, 1]) {
      translate([0, i*contact_x*1.5, displacement_z-contact_z+eps]) {
        cube([contact_x, .5, contact_z], center=false);
      }
    }
  }
  echo("Body Height:", body_z, "Total Height:", body_z+contact_z, "Internal Clearance:", body_z+contact_z-button_z-flange_z);
}

module arcadeSwitchCutter(body_d=30, $fn=128) {
  cylinder(h=2, d=body_d, center=true);
}

// arcadeSwitch();
// arcadeSwitchCutter();
