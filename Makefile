.PHONY: update update-clean

# 虚拟机上：拉代码并重建镜像
update:
	./update.sh

# 前端样式仍是旧的时，丢掉构建缓存再编
update-clean:
	./update.sh --no-cache
