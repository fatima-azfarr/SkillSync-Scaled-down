# SkillSync Frontend — Nginx static file server
# Serves the HTML/CSS/JS files on port 80

FROM nginx:alpine

# Copy our frontend files to the nginx html directory
COPY . /usr/share/nginx/html/

# Remove Dockerfile from served files
RUN rm -f /usr/share/nginx/html/Dockerfile

# Expose port 80
EXPOSE 80
