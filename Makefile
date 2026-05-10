run:
	cd rust-core && cargo build --release
	cd ..

fix:
	python cli.py fix "bug in project"

voice:
	python cli.py voice

rust:
	cd rust-core && cargo build --release && cd ..
