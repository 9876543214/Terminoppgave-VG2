$(function() {
    $('a#like_button').on('click', async function(e) {
        e.preventDefault();
        let post_id = this.className;
        let like_id = "like_" + post_id;
        var like_button = document.getElementById(like_id);
        var likecount = document.getElementById('like_amount_' + post_id);
        var likecount_int = Number(likecount.textContent)
        var like_src = like_button.src
        try {
            let data = $.getJSON('/addlike?post_id=' + post_id);
            console.log(like_src)

            if (like_src === "http://10.0.0.32:5000/static/img/favorite_20dp_000000_FILL0_wght400_GRAD0_opsz20.svg") {
                like_button.src = "static/img/favorite_20dp_EA3323_FILL1_wght400_GRAD0_opsz20.svg";
                likecount_int = likecount_int + 1
            } else {
                like_button.src = "static/img/favorite_20dp_000000_FILL0_wght400_GRAD0_opsz20.svg";
                likecount_int = likecount_int - 1
            }

            var likecount_content = likecount_int.toString()

            likecount.textContent = likecount_content


        } catch (error) {
            console.error("Error:", error);
        }
    });
});

$(function() {
    $('a#comment_button').on('click', async function(e) {
        e.preventDefault()
        let comment_section = document.getElementById("comment_section")
        let post_id = this.className
        let comment_id = "comment_" + post_id
        var comment_count = document.getElementById('like_amount_' + post_id)
        var comment_count_int = Number(comment_count.textContent)
        console.log("1")
        try {
            let comments = await $.getJSON('/opencomments?post_id=' + post_id)
            let comment_section = document.getElementById('comment_section')

            console.log(comments)

            
            if (comment_section.style.display === "" || comment_section.style.display === "none") {
                comment_section.style.display = "flex"
                comments.forEach(comment => {
                    console.log(comment)
                    comment_section.innerHTML += `                            
                        <div class="${comment.comment_id} comment" id="comment_${comment.post_id}">
                            <h4>${comment.username}</h4>
                            <p>${comment.content}</p>
                        </div>
                        <div id="line"></div>` 
            });
            } else {
                console.log("comment_" + comments[0].post_id)                
                if (comments[0] != null) {
                    comments.forEach(comment => {
                        let comments2 = document.getElementById("comment_" + comments[0].post_id)
                        let line = document.getElementById("line")
                        comments2.remove()
                        line.remove()
                    });
                    
                }
                comment_section.style.display = "none"

            }


        } catch (error) {
            console.error("Error: ", error)
        }
                
    })
})