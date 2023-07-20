from streamlit.components.v1 import html
import streamlit as st
import base64
from pathlib import Path
def load_bootstrap():
    return st.markdown('<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">', unsafe_allow_html=True)
def img_to_bytes(img_path):
    img_bytes = Path(img_path).read_bytes()
    encoded = base64.b64encode(img_bytes).decode()
    return encoded
def img_to_html(img_path):
    img_html = "<img src='data:image/png;base64,{}' class='img-fluid'>".format(
      img_to_bytes(img_path)
    )
    return img_html
def header(path_to_logo,title):
    
    col1,col2,col3=st.columns([1,1,1])
    with col2:
        st.markdown(img_to_html(f'{path_to_logo}'), unsafe_allow_html=True)
    st.title(title)

def _inject_page_script(page_name, action_script, timeout_secs=3):
    page_script = """
        <script type="text/javascript">
            function attempt_exec_page_action(page_name, start_time, timeout_secs, action_fn) {
                var links = window.parent.document.getElementsByTagName("a");
                for (var i = 0; i < links.length; i++) {
                    if (links[i].href.toLowerCase().endsWith("/" + page_name.toLowerCase())) {
                        action_fn(links[i]);
                        return;
                    }
                }
                var elasped = new Date() - start_time;
                if (elasped < timeout_secs * 1000) {
                    setTimeout(attempt_exec_page_action, 100, page_name, start_time, timeout_secs, action_fn);
                } else {
                    alert("Unable to locate link to page '" + page_name + "' after " + timeout_secs + " second(s).");
                }
            }
            window.addEventListener("load", function() {
                attempt_exec_page_action("%s", new Date(), %d, function(link) {
                    %s
                });
            });
        </script>
    """ % (page_name, timeout_secs, action_script)
    html(page_script, height=0)
def hide_page(page_name, **kwargs):
    _inject_page_script(page_name, 'link.style.display = "none";', **kwargs)
def nav_page(page_name, timeout_secs=3):
    nav_script = """
        <script type="text/javascript">
            function attempt_nav_page(page_name, start_time, timeout_secs) {
                var links = window.parent.document.getElementsByTagName("a");
                for (var i = 0; i < links.length; i++) {
                    if (links[i].href.toLowerCase().endsWith("/" + page_name.toLowerCase())) {
                        links[i].click();
                        return;
                    }
                }
                var elasped = new Date() - start_time;
                if (elasped < timeout_secs * 1000) {
                    setTimeout(attempt_nav_page, 100, page_name, start_time, timeout_secs);
                } else {
                    alert("Unable to navigate to page '" + page_name + "' after " + timeout_secs + " second(s).");
                }
            }
            window.addEventListener("load", function() {
                attempt_nav_page("%s", new Date(), %d);
            });
        </script>
    """ % (page_name, timeout_secs)
    html(nav_script)