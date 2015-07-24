/**
 * Created by haribala on 4/22/2015.
 */

var search_all_clicked = 0;

var main = function() {
    /* Push the body and the nav over by 285px over */
    var add_books_counter = 0;
    var is_mobile = false;

    $('#more_lend_books').click(function(){

        if (add_books_counter < 5) {
            var namestring = "bookname";
            namestring = namestring + add_books_counter;

            var x = document.forms["name_lend_form"][namestring].value;
            if (x == null || x == "") {
                alert("Name must be filled out");
                return;
            }

            add_books_counter = add_books_counter + 1;
            var namestring = "bookname" + add_books_counter;

            var controlstring = "Book Name: <input type='text' value='' ";
            controlstring = controlstring + "name=" + namestring + "> <br>";
           $('#more_lend_books').before(controlstring);
        } else {
            /* disable the "more_lend_books" button, only "submit" would be valid. */
            $("#more_lend_books").hide();
        }

    });

    $('#search_book_entry').mouseover(function(){
        $('#all_borrow_books').hide();
        search_all_clicked = 0;
    });
    $('#search_book_entry').mouseleave(function(){
        $('#all_borrow_books').show();
    });

    $('#all_borrow_books').mouseover(function(){
        $('#search_book_entry').hide();
        search_all_clicked = 1;
    });
    $('#all_borrow_books').mouseleave(function(){
        $('#search_book_entry').show();
    });

    /* 
    var cookie = document.cookie;
    alert ("cookie was:" + cookie)
    */

    is_mobile = window.matchMedia("only screen and (max-width: 760px)");
    if (is_mobile.matches) {
        // in Android code, there is corresponding function
        // that has been written to return the string.
        //var output = Android.showToast("How are you?");
        //$('#fake_login_button_id').val(output);
    }
       
    //alert("I should be seen everywhere");

    //check if URL is lend_books; if so and mobile device, add a new button called "scan ISBN"
    var loc = location.href;
    var is_lend = loc.indexOf("lend_books");
    if (is_lend != -1 &&  is_mobile.matches) {
        $('#search_books_form').append('<input type="submit" name="scan" value="scan" id="scan_id">');
        $('#scan_id').click(function() {
            var output = Android.showToast("How are you?");
            //assume the output is the name of the book to upload to the server.
            var xmlhttp;

            xmlhttp=new XMLHttpRequest();
            xmlhttp.open("POST","",false);
            xmlhttp.setRequestHeader("Content-type","application/x-www-form-urlencoded");
            xmlhttp.send("bookname0=FromJSScript");
        });
    } 
}

function validateForm() {
    var x = document.forms["name_search_form"]["bookname"].value;
    if (search_all_clicked == 0 && (x == null || x == "")) {
        alert("Name must be filled out");
        return false;
    }
}

$(document).ready(main);
