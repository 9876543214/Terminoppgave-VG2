const validation = new JustValidate("#register");
let emailValidationCache = {};

validation
    .addField("#name", [
        {
            rule: "required"
        }
    ])
    .addField("#email", [
        {
            rule: "required"
        },
        {
            rule: "email"
        },
        {
            validator: (value) => {
                // Use a cached value or mark as invalid if not checked yet
                if (emailValidationCache[value] === undefined) {
                    // Perform async check in the background
                    fetch("http://10.2.3.64:5000/validate_email?email=" + encodeURIComponent(value))
                        .then((response) => response.json())
                        .then((json) => {
                            emailValidationCache[value] = !json.exists; // Cache result
                        })
                        .catch(() => {
                            emailValidationCache[value] = false; // Assume invalid on error
                        });
        
                    return true; // Optimistically allow; validation will happen eventually
                }
        
                return emailValidationCache[value]; // Return cached result
            },
            errorMessage: "Email is already in use",
        }
    ])
    .addField("#password", [
        {
            rule: "required"
        },
        {
            rule: "password"
        }
    ])
    .addField("#password_confirmation", [
        {
            validator: (value, fields) => {
                return value === fields["#password"].elem.value;
            },
            errorMessage: "Passwords must match"
        }
    ])
    .onSuccess((event) => {
        document.getElementById("register").submit();
    });