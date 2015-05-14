/**
 * Created by haribala on 4/22/2015.
 */

var search_all_clicked = 0;

var main = function() {
    /* Push the body and the nav over by 285px over */
    var add_books_counter = 0;

    /*
    $('.bigTitle').click(function () {
        $('body').animate({
            left: "285px", height: "100px", fontSize: "3em"
        }, 200);
        var x = document.getElementsByClassName("bigTitle");
        x[0].style.color = "green";

    });
    $('.books_list').click(function () {
        $('.book_entry').animate({
            fontSize: "3em"
        }, 200);

    });
    */

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
}

function validateForm() {
    var x = document.forms["name_search_form"]["bookname"].value;
    if (search_all_clicked == 0 && (x == null || x == "")) {
        alert("Name must be filled out");
        return false;
    }
}

$(document).ready(main);
