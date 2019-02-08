
#!/usr/bin/perl
use strict;
use warnings;

# Ask for password
my $password = getPass();

# Check the password
checkPass($password);


sub getPass {
  print("Enter your password: ");
  my $password = <STDIN>;
  chomp $password;
  return $password
}

sub checkPass {
  my ($pass) = @_;
  my $len = length($pass);

  # Check if length is at least 8 characters
  if ($len < 8) {
    print("Password must be at least 8 characters.\n");
    return;

  # If between 8 and 11
  } elsif (8 <= $len && $len <= 11) {
    
    if (not hasUpper()) {
      print("You need at least one upper case letter\n");
    };

    if (not hasLower()) {
      print("You need at least one lowercase letter\n")
    };
    
    if (not hasNumber()) {
      print("You need at least one number\n")
    };

    if (not hasSpecial()) {
      print("You need at least one special character\n")
    };

    return 1;

  # If between 12-15
  } elsif (12 <= $len && $len <= 15) {
    
    if (not hasUpper()) {
      print("You need at least one upper case letter\n");
    };

    if (not hasLower()) {
      print("You need at least one lowercase letter\n")
    };
    
    if (not hasNumber()) {
      print("You need at least one number\n")
    };

    return 1;

  # If between 16 - 19
  } elsif (16 <= $len && $len <= 19) { 
    if (not hasUpper()) {
      print("You need at least one upper case letter\n");
    };
    if (not hasLower()) {
      print("You need at least one lowercase letter\n")
    };
    return 1;

  } elsif ($len <= 20) {
    # Do nothing
    return 1;

  };
}

# Checks for upper case
sub hasUpper {
  if ($password =~ /[A-Z]/) {
    return 1;
  }
}

# Checks for lower case
sub hasLower {
  if ($password =~ /[a-z]/) {
    return 1;
  }
}

# Checks for a numbers
sub hasNumber {
  if ($password =~ /[1-9]/) {
    return 1;
  }
}

# Checks for special characters
sub hasSpecial {
  if ($password =~ /\W/) {
    return 1;
  }
}
