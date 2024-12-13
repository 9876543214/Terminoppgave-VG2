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
            

            if (like_src === "http://10.2.3.64:5000/static/img/favorite_20dp_000000_FILL0_wght400_GRAD0_opsz20.svg") {
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
        post_id = this.className
        try {
            let comments = await $.getJSON('/opencomments?post_id=' + post_id)
            let comment_section = document.getElementById('comment_section')

            console.log(comments)

            comment_section.innerHTML += `
                            <form action="submit_comment" method="post" enctype="multipart/form-data" class="new-comment">
                                <textarea placeholder="" rows="3" id="commentContent" name="content"></textarea>
                                <button type="submit">Comment</button>
                            </form>
            `
            
            // comments.array.forEach(comment => {
            //     print(comment)
            //     comment_section.innerHTML += `                            
            //         <div class="${comment.comment_id} comment">
            //             <h4>{{comment.username}}</h4>
            //             <p>{{comment.content}}</p>
            //         </div>`
            // });
        } catch (error) {
            console.error("Error: ", error)
        }
                
    })
})