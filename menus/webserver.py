from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi

# imports for CRUD Operations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Restaurant, Base, MenuItem

# Create session and connect to DB
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


class webserverHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            if self.path.endswith("/restaurants"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                restaurants = session.query(Restaurant).all()

                output = ""
                output += "<html><body>"

                for restaurant in restaurants:
                    output += '''
                    <p><b>%s</b>
                    <br>
                    <a href="/restaurant/%s/edit">Edit</a> | <a href="/restaurant/%s/delete">Delete</a></p>
                    ''' % (restaurant.name, restaurant.id, restaurant.id)

                output += "<p><a href=\"/restaurants/new\">Create a new restaurant</a>"

                output += "</body></html>"

                self.wfile.write(output)
                print output

                return

            if self.path.endswith("/restaurants/new"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                output = ""
                output += "<html><body>"

                output += '''
                <h2>What's the name of the restaurant?</h2>
                <form method='POST' enctype='multipart/form-data' action='/restaurants/new'>
                    <input name='restaurant_name' type='text' placeholder='New Restaurant Name'>
                    <input type='submit' value='Create'>
                </form>
                '''
                output += "<p><a href=\"/restaurants\">Cancel</a></p>"
                output += "</body></html>"

                self.wfile.write(output)
                print output

                return

            if self.path.endswith("/edit"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                restaurantID = self.path.split("/")[2]
                restaurant = session.query(Restaurant).filter_by(id = restaurantID).one()

                output = ""
                output += "<html><body>"

                output += '''
                <h2>%s</h2>
                <form method='POST' enctype='multipart/form-data' action='/restaurants/%s/edit'>
                    <input name='restaurant_name' type='text' placeholder='New Restaurant Name'>
                    <input type='submit' value='Rename'>
                </form>
                ''' % (restaurant.name, restaurant.id)
                output += "<p><a href=\"/restaurants\">Cancel</a></p>"
                output += "</body></html>"

                self.wfile.write(output)
                print output

                return

            if self.path.endswith("/delete"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                restaurantID = self.path.split("/")[2]
                restaurant = session.query(Restaurant).filter_by(id = restaurantID).one()

                output = ""
                output += "<html><body>"

                output += '''
                <h2>Are you sure you want to delete %s?</h2>
                <form method='POST' enctype='multipart/form-data' action='/restaurants/%s/delete'>
                    <input type='submit' value='Delete'>
                </form>
                ''' % (restaurant.name, restaurant.id)
                output += "<p><a href=\"/restaurants\">Cancel</a></p>"
                output += "</body></html>"

                self.wfile.write(output)
                print output

                return

        except IOError:
            self.send_error(404, "File not found %s" % self.path)

    def do_POST(self):
        try:
            if self.path.endswith("/restaurants/new"):

                self.send_response(301)
                self.send_header('Content-type', 'text/html')
                self.send_header('Location', '/restaurants')
                self.end_headers()

                ctype, pdict = cgi.parse_header(
                    self.headers.getheader("content-type")
                )
                if ctype == "multipart/form-data":
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    messagecontent = fields.get('restaurant_name')

                    # Create new Restaurant
                    newRestaurant = Restaurant(name = messagecontent[0])
                    session.add(newRestaurant)
                    seesion.commit()

                return

            if self.path.endswith("/edit"):

                self.send_response(301)
                self.send_header('Content-type', 'text/html')
                self.send_header('Location', '/restaurants')
                self.end_headers()

                ctype, pdict = cgi.parse_header(
                    self.headers.getheader("content-type")
                )
                if ctype == "multipart/form-data":
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    messagecontent = fields.get('restaurant_name')

                    # Update Restaurant
                    restaurantID = self.path.split("/")[2]
                    restaurant = session.query(Restaurant).filter_by(id = restaurantID).one()
                    if restaurant != []:
                        restaurant.name = messagecontent[0]
                        session.add(restaurant)
                        seesion.commit()

                return

            if self.path.endswith("/delete"):

                self.send_response(301)
                self.send_header('Content-type', 'text/html')
                self.send_header('Location', '/restaurants')
                self.end_headers()

                ctype, pdict = cgi.parse_header(
                    self.headers.getheader("content-type")
                )
                if ctype == "multipart/form-data":
                    # Update Restaurant
                    restaurantID = self.path.split("/")[2]
                    restaurant = session.query(Restaurant).filter_by(id = restaurantID).one()
                    if restaurant != []:
                        session.delete(restaurant)
                        seesion.commit()sh

                return

        except:
            pass


def main():
    try:
        port = 8080
        server = HTTPServer(('', port), webserverHandler)
        print "Web server is running on port %s" % port
        server.serve_forever()

    except KeyboardInterrupt:
        print "^C entered, stopping web server..."
        server.socket.close()

if __name__ == '__main__':
    main()
