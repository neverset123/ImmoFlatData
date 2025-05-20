git config user.name "neverset123"
git config user.email "neverset@aliyun.com"
git filter-branch -f --commit-filter '                                          
        if [ "$GIT_COMMITTER_EMAIL" = "" ];         
        then                                                                    
                GIT_COMMITTER_NAME="neverset123";                               
                GIT_AUTHOR_NAME="neverset123";                                  
                GIT_COMMITTER_EMAIL="neverset@aliyun.com";                      
                GIT_AUTHOR_EMAIL="neverset@aliyun.com";                         
                git commit-tree "$@";                                           
        else                                                                    
                git commit-tree "$@";                                           
        fi' HEAD
git push --force --tags origin 'refs/heads/main'